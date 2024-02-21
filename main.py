from eth_account import Account
from loguru import logger as log
from web3 import Web3
import time
import random
import sys


web3 = Web3(Web3.HTTPProvider("https://bsc-testnet.publicnode.com"))


class FileManager:
    def __init__(self, filename):
        self.filename = filename

    def read_lines(self):
        lines = []
        with open(self.filename, "r") as file:
            for line in file:
                lines.append(line.strip())
        return lines

    def clear_file(self):
        with open(self.filename, "w") as file:
            file.write("")
        file.close()

    def save_to_txt(self, name, address, private_key):
        with open(self.filename, "a") as file:
            file.write(f"{name}:{address}:{private_key}\n")
        file.close()

    def count_lines_in_file(self):
        with open(self.filename, "r", encoding="UTF-8") as file:
            return sum(1 for line in file)

    def get_all_wallet_data_from_file(self):
        wallet_data_list = []
        with open(self.filename, "r") as file:
            for line in file:
                parts = line.strip().split(":")
                wallet_data = {
                    "name": parts[0],
                    "address": parts[1],
                    "private_key": parts[2],
                }
                wallet_data_list.append(wallet_data)
        return wallet_data_list

    def get_private_key_main_from_file(self, filename):
        with open(filename, "r") as file:
            return file.readline().strip()


def create_new_ethereum_wallet(name):
    new_account = Account.create()
    address = new_account.address.strip()
    private_key = new_account._private_key.hex().strip()
    return name, address, private_key


def random_time(min, max):
    return random.randint(min, max)


def sign_my_tx(my_tx, private_key):
    try:
        gas_limit = int(
            web3.eth.estimate_gas(my_tx) * (1 + random.randint(1, 100) / 100)
        )
        gas_price = int(web3.eth.gas_price * (1 + random.randint(1, 100) / 100))

        if my_tx["gas"] == 0 and my_tx["gasPrice"] == 0:
            my_tx["gas"] = gas_limit
            my_tx["gasPrice"] = gas_price

        signed_transaction = web3.eth.account.sign_transaction(
            my_tx, private_key=private_key
        )
        return signed_transaction
    except Exception as e:
        log.error(f"Error signing transaction: {e}")
        return None


def send_bnb(private_key, address_to, amount):
    sender_address = Account.from_key(private_key_main)
    sender_address = Web3.to_checksum_address(sender_address.address)
    transfer_tx = {
        "to": address_to,
        "value": amount,
        "gas": 21000,
        "gasPrice": 10000000000,
        "nonce": web3.eth.get_transaction_count(sender_address),
        "chainId": 97,
    }

    signed_tx = sign_my_tx(transfer_tx, private_key)
    if signed_tx is not None:
        try:
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            log.info(f"Transaction hash: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            log.error(f"Transaction failed: {str(e)}")
            return False
    else:
        log.error("Transaction signing failed.")
        return False


def create_wallets(file_manager):
    existing_lines = file_manager.count_lines_in_file()

    log.info("How many wallets do you need?:")
    try:
        input_range = int(input())
        if input_range < 1 or input_range > 100:
            raise ValueError("Number of wallets must be a positive integer or 100 max")

        for i in range(existing_lines + 1, existing_lines + input_range + 1):
            wallet_name, new_wallet_address, new_wallet_private_key = (
                create_new_ethereum_wallet(f"{i}")
            )
            file_manager.save_to_txt(
                wallet_name,
                new_wallet_address,
                new_wallet_private_key,
            )
        log.info(f"{input_range} wallets created successfully.")
    except ValueError as e:
        log.error(f"Invalid input: {e}")


def delete_wallets(file_manager):
    confirm_delete = input("Are you sure you want to delete the wallets file? (y/n): ")
    log.info(f"Confirm delete: {confirm_delete}")

    if confirm_delete.lower() == "y":
        log.info("User confirmed deletion.")
        file_manager.clear_file()
    elif confirm_delete.lower() == "n":
        log.info("User cancelled deletion.")
    else:
        log.warning("Invalid input. Please enter 'y' or 'n'.")


def send_bnb_to_wallets(file_manager, private_key_main):
    wallet_data = file_manager.get_all_wallet_data_from_file()
    amount_str = input("Amount BNB to send: ")
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError("Amount must be a positive number")
    except ValueError:
        log.error("Invalid amount. Please enter a valid number.")
        return

    for i, wallet in enumerate(wallet_data, start=1):
        amount_wei = Web3.to_wei(amount, "ether")
        log.info(f"{i}. {wallet['address']}")
        send_bnb(private_key_main, wallet["address"], amount_wei)
        sleeping_time = random_time(5, 10)
        log.info(f"Wait {sleeping_time} second")
        time.sleep(sleeping_time)


def claim_faucet(sender_address, private_key):
    contract_address = Web3.to_checksum_address(
        "0x3cC6FC1035465d5b238F04097dF272Fe9b60EB94"
    )

    sender_address = Account.from_key(private_key)
    sender_address = Web3.to_checksum_address(sender_address.address)

    data_to_send = f"0xee42b5c7000000000000000000000000{sender_address[2:].lower()}000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000001300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000013000000000000000000000000000000000000000000000000000000000000000"
    transaction_faucet = {
        "from": sender_address,
        "to": contract_address,
        "value": 0,
        "gas": 0,
        "gasPrice": 0,
        "nonce": web3.eth.get_transaction_count(sender_address),
        "data": data_to_send,
        "chainId": 97,
    }

    signed_tx = sign_my_tx(transaction_faucet, private_key)
    if signed_tx is not None:
        try:
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            log.info(f"Transaction hash: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            log.error(f"Transaction failed: {str(e)}")
            return False
    else:
        log.error("Transaction signing failed.")
        return False


def claim_faucet_to_wallets(file_manager):

    wallet_data = file_manager.get_all_wallet_data_from_file()

    for i, wallet in enumerate(wallet_data, start=1):
        log.info(f"{i}. {wallet['address']}")
        claim_faucet(wallet["address"], wallet["private_key"])
        sleeping_time = random_time(5, 10)
        log.info(f"Wait {sleeping_time} second")
        time.sleep(sleeping_time)


if __name__ == "__main__":

    file_manager = FileManager("ethereum_wallet.txt")

    private_key_main = file_manager.get_private_key_main_from_file("private_main.txt")
    while True:
        log.info("\033[32m1. Create wallets\033[0m")
        log.info("2. Delete new wallets")
        log.info("3. Send BNB to new wallets from main")
        log.info("4. Claim tokens Nulink")
        log.info("\033[31m10. Exit\033[0m")
        choice = input("Enter your choice: ")

        if choice == "1":
            create_wallets(file_manager)
        if choice == "2":
            delete_wallets(file_manager)
        if choice == "3":
            send_bnb_to_wallets(file_manager, private_key_main)
        if choice == "4":
            claim_faucet_to_wallets(file_manager)

        if choice == "10":
            log.info("\033[31mExiting...\033[0m")
            break
        else:
            break
