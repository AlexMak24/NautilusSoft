from web3 import Web3
import json

# Подключение к узлу Nautilus Chain (замените на фактический узел Nautilus)
nautilus_url = "https://api.nautilus.nautchain.xyz"
web3 = Web3(Web3.HTTPProvider(nautilus_url))

# Проверка подключения
if not web3.is_connected():
    raise Exception("Не удалось подключиться к узлу Nautilus Chain")

# ABI контракта (только нужная часть)
abi = [
{
        "constant": True,
        "inputs": [
            {
                "name": "_owner",
                "type": "address"
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "name": "balance",
                "type": "uint256"
            }
        ],
        "type": "function"
    },
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

# Адреса и значения
from_address = ''
contract_address = '0xB2723928400AE5778f6A3C69D7Ca9e90FC430180'
value_in_ether = 1
# Приватный ключ отправителя
private_key = ''

# Создание экземпляра контракта
contract = web3.eth.contract(address=contract_address, abi=abi)

# Получение актуального значения nonce
actual_nonce = web3.eth.get_transaction_count(from_address)

# Подготовка данных для метода
destination = 56  # Chain ID для BSC
recipient = ''
recipient_checksum = web3.to_checksum_address(recipient) # Преобразование в checksum address
print("checksum address: ", recipient_checksum)
amount = web3.to_wei(value_in_ether, 'ether')

# Преобразование адреса в bytes32
recipient_bytes32 = Web3.to_bytes(hexstr=recipient_checksum).rjust(32, b'\0')

balance = contract.functions.balanceOf(from_address).call()
print(f"Your balance: {balance / (10 ** 18)} USDC")

# Проверка баланса отправителя
balance = web3.eth.get_balance(from_address)
print(f"Текущий баланс: {web3.from_wei(balance, 'ether')} Ether")

# Получение актуального значения Gas Limit
latest_block = web3.eth.get_block('latest')
print(f"Gas Limit последнего блока: {latest_block['gasLimit']}")
gas_limit = latest_block['gasLimit']

# Получение текущей цены газа
current_gas_price = web3.eth.gas_price
gas_price_in_gwei = web3.from_wei(current_gas_price, 'gwei')
print(f"Текущая цена газа (Gwei): {gas_price_in_gwei}")

# Расчет стоимости газа для транзакции
gas_fee = current_gas_price * gas_limit
total_cost = amount + gas_fee

if balance < total_cost:
    raise Exception(f"Недостаточно средств. Баланс: {web3.from_wei(balance, 'ether')} ETH, требуется: {web3.from_wei(total_cost, 'ether')} ETH")

gas_payment = contract.functions.quoteGasPayment(destination).call()
print(f"Gas payment: {gas_payment}")

# Создание транзакции с актуальным значением nonce
transaction = contract.functions.transferRemote(destination, recipient_bytes32, amount).build_transaction({
    'from': from_address,
    'nonce': actual_nonce,  # Использование актуального значения nonce
    'gas': gas_limit,
    'gasPrice': current_gas_price,
    'value': amount + gas_payment  # Передача общей суммы
})

# Подпись транзакции
signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)

# Отправка транзакции
try:
    txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Транзакция отправлена с хешем: {web3.to_hex(txn_hash)}")
except ValueError as e:
    print(f"Ошибка при отправке транзакции: {e}")
    # Получение дополнительной информации о причине ошибки
    error_data = e.args[0]
    print(f"Данные ошибки: {error_data}")
