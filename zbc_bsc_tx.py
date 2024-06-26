from web3 import Web3
from eth_account import Account

# Подключение к сети BSC
w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed1.binance.org:443'))

# Загрузка аккаунта из приватного ключа
private_key = ''
account = Account.from_key(private_key)

# Адрес контракта моста и ABI
bridge_contract_address = '0xC27980812E2E66491FD457D488509b7E04144b98'
bridge_abi = [
    {
        "inputs": [
            {
                "internalType": "uint32",
                "name": "_destinationDomain",
                "type": "uint32"
            }
        ],
        "name": "quoteGasPayment",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "_gasPayment",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint32",
                "name": "_destination",
                "type": "uint32"
            },
            {
                "internalType": "bytes32",
                "name": "_recipient",
                "type": "bytes32"
            },
            {
                "internalType": "uint256",
                "name": "_amountOrId",
                "type": "uint256"
            }
        ],
        "name": "transferRemote",
        "outputs": [
            {
                "internalType": "bytes32",
                "name": "messageId",
                "type": "bytes32"
            }
        ],
        "stateMutability": "payable",
        "type": "function"
    }
]

# Адрес контракта токена ZBC и ABI
token_contract_address = '0x37a56cdcD83Dce2868f721De58cB3830C44C6303'
token_abi = [
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

# Создание экземпляров контрактов
bridge_contract = w3.eth.contract(address=bridge_contract_address, abi=bridge_abi)
token_contract = w3.eth.contract(address=token_contract_address, abi=token_abi)

# Параметры для функции transferRemote
destination_network_id = 22222  # Идентификатор сети Nautilus
recipient_address = '0x5E2fd51a1881116142a1e4E051Aa973c65763CE2'  # Адрес получателя на сети Nautilus

amount = 1660444098731336109  # 1.6 токенов ZBC (с учетом десятичных знаков)

# Преобразование адреса получателя в bytes32
recipient_bytes32 = Web3.to_bytes(hexstr=recipient_address).rjust(32, b'\0')

# Проверка баланса
balance = token_contract.functions.balanceOf(account.address).call()
bnb_balance = w3.eth.get_balance(account.address)
print(f"Token balance: {balance}")
print(f"BNB balance: {bnb_balance}")

if balance < amount:
    raise Exception("Insufficient token balance")
if bnb_balance < w3.to_wei('0.001', 'ether'):  # Убедитесь, что достаточно BNB для комиссии
    raise Exception("Insufficient BNB balance")

# Шаг 1: Одобрение токенов для контракта моста
nonce = w3.eth.get_transaction_count(account.address)
tx_approve = token_contract.functions.approve(bridge_contract_address, amount).build_transaction({
    'from': account.address,
    'nonce': nonce,
    'gas': 100000,  # Установите подходящий лимит газа
    'gasPrice': w3.to_wei('5', 'gwei'),  # Установите подходящую цену газа
})
signed_tx_approve = w3.eth.account.sign_transaction(tx_approve, private_key)
tx_approve_hash = w3.eth.send_raw_transaction(signed_tx_approve.rawTransaction)
print("Approve transaction hash:", tx_approve_hash.hex())

# Подождите, пока транзакция будет включена в блок
approve_receipt = w3.eth.wait_for_transaction_receipt(tx_approve_hash)
if approve_receipt.status != 1:
    raise Exception("Approve transaction failed")

# Шаг 2: Определите необходимую оплату газа
gas_payment = bridge_contract.functions.quoteGasPayment(destination_network_id).call()
print(f"Gas payment: {gas_payment}")

# Шаг 3: Выполните межцепочечную транзакцию
nonce += 1
tx_transfer_remote = bridge_contract.functions.transferRemote(
    destination_network_id,
    recipient_bytes32,  # Используем bytes32 адрес
    amount
).build_transaction({
    'from': account.address,
    'nonce': nonce,
    'value': gas_payment,  # Добавляем необходимую оплату газа
    'gas': 200000,  # Установите подходящий лимит газа
    'gasPrice': w3.to_wei('5', 'gwei'),  # Установите подходящую цену газа
})
signed_tx_transfer_remote = w3.eth.account.sign_transaction(tx_transfer_remote, private_key)
tx_transfer_remote_hash = w3.eth.send_raw_transaction(signed_tx_transfer_remote.rawTransaction)
print("Transfer remote transaction hash:", tx_transfer_remote_hash.hex())

# Подождите, пока транзакция будет включена в блок
transfer_receipt = w3.eth.wait_for_transaction_receipt(tx_transfer_remote_hash)
if transfer_receipt.status != 1:
    raise Exception("Transfer remote transaction failed")
