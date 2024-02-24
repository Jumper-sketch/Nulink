from eth_account import Account
from loguru import logger as log
from web3 import Web3
import time
import random
import sys
import json


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
                if len(parts) == 3:
                    wallet_data = {
                        "name": parts[0],
                        "address": parts[1],
                        "private_key": parts[2],
                    }
                elif len(parts) == 1:
                    wallet_data = {
                        "name": None,
                        "address": None,
                        "private_key": parts[0],
                    }
                else:
                    continue
                wallet_data_list.append(wallet_data)
        return wallet_data_list


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
    except ValueError as e:
        log.error(f"Error signing transaction: {e}")
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}")
    return None


def send_bnb(private_key, address_to, amount):
    sender_address = Account.from_key(private_key)
    sender_address = Web3.to_checksum_address(sender_address.address)
    transfer_tx = {
        "to": address_to,
        "value": amount,
        "gas": 0,
        "gasPrice": 0,
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


def send_bnb_to_wallets(file_manager, private_key):
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
        send_bnb(private_key, wallet["address"], amount_wei)
        sleeping_time = random_time(5, 10)
        log.info(f"Wait {sleeping_time} second")
        time.sleep(sleeping_time)


def claim_faucet(sender_address, private_key):
    with open("abi/contracts.json", "r") as json_file:
        data = json.load(json_file)
    contract_address = data["contract_address"]

    sender_address = Web3.to_checksum_address(Account.from_key(private_key).address)

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
        sleeping_time = random_time(20, 50)
        log.info(f"Wait {sleeping_time} second")
        time.sleep(sleeping_time)


def get_pending_user_reward(private_key):
    with open("abi/contracts.json", "r") as json_file:
        data = json.load(json_file)
    with open("abi/nulink.json", "r") as file:
        nulink_abi = json.load(file)
    sender_address = Web3.to_checksum_address(Account.from_key(private_key).address)

    stake_contract_address = data["stake_contract_address"]
    stake_contract = web3.eth.contract(address=stake_contract_address, abi=nulink_abi)

    try:
        pending_reward = stake_contract.functions.pendingUserReward(
            sender_address
        ).call()
        pending_reward = Web3.from_wei(pending_reward, "ether")
        pending_reward_rounded = round(pending_reward, 3)
        return pending_reward_rounded
    except Exception as e:
        return None


def get_pending_user_reward_wallets(file_manager):
    wallet_data = file_manager.get_all_wallet_data_from_file()

    for i, wallet in enumerate(wallet_data, start=1):
        rewards = get_pending_user_reward(wallet["private_key"])
        wallet_address = Web3.to_checksum_address(
            Account.from_key(wallet["private_key"]).address
        )
        log.info(f"{i}. Rewards {wallet_address} {rewards} Nulink")


def get_token_balance(token_address, wallet_address):
    with open("abi/contracts.json", mode="r", encoding="utf-8") as contracts:
        contracts = json.load(contracts)
    with open("abi/erc20.json", mode="r", encoding="utf-8") as erc20_abi:
        erc20_abi = json.load(erc20_abi)

    contract_address = Web3.to_checksum_address(token_address)

    contract = web3.eth.contract(address=contract_address, abi=erc20_abi)
    wallet_address = Web3.to_checksum_address(wallet_address)
    balance = contract.functions.balanceOf(wallet_address).call()

    return balance


def stake(private_key):
    with open("abi/contracts.json", mode="r", encoding="utf-8") as contracts:
        contracts = json.load(contracts)
    with open("abi/nulink.json", mode="r", encoding="utf-8") as json_file:
        nulink_abi = json.load(json_file)

    stake_contract_address = contracts["stake_contract_address"]
    nulink_token_address = contracts["nulink_token_address"]

    sender_address = Web3.to_checksum_address(Account.from_key(private_key).address)
    log.info(sender_address)

    stake_contract = web3.eth.contract(address=stake_contract_address, abi=nulink_abi)

    amount = get_token_balance(nulink_token_address, sender_address)
    amount_nulink = amount / 10**18
    log.info(f"Staking amount: {amount_nulink}")

    if amount_nulink > 1:
        random_subtract = random.uniform(0.001, 0.1)
        amount -= int(random_subtract * 10**18)
        log.info(f"Subtracted amount: {random_subtract}")

        nonce = web3.eth.get_transaction_count(sender_address)

        stake_tx = stake_contract.functions.stake(
            sender_address, sender_address, sender_address, amount
        ).build_transaction(
            {
                "from": sender_address,
                "gas": 0,
                "nonce": nonce,
                "gasPrice": 0,
                "chainId": 97,
            }
        )
        signed_tx = sign_my_tx(stake_tx, private_key)
        if signed_tx is not None:
            try:
                tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                log.info(f"Transaction hash: {tx_hash.hex()}")
                return True
            except Exception as e:
                log.error(f"Transaction failed: {str(e)}")
                return False
        else:
            log.error("Transaction signing failed.")
            return False
    else:
        log.info(f"Amount Nulink token is: {amount_nulink} NLK. Not need stake")
        return False


def stake_wallets(file_manager):
    wallet_data = file_manager.get_all_wallet_data_from_file()

    for i, wallet in enumerate(wallet_data, start=1):
        approve = approve_token_spending(wallet["private_key"])
        if approve:
            log.info("Approve done.")
            sleeping_time = random_time(10, 20)
            stake_checker = stake(wallet["private_key"])
            if stake_checker:
                sleeping_time = random_time(10, 30)
                log.info(f"Wait {sleeping_time} second")
                time.sleep(sleeping_time)


def claim_rewards(private_key):
    with open("abi/contracts.json", mode="r", encoding="utf-8") as contracts:
        contracts = json.load(contracts)
    with open("abi/nulink.json", mode="r", encoding="utf-8") as json_file:
        nulink_abi = json.load(json_file)

    sender_address = Web3.to_checksum_address(Account.from_key(private_key).address)
    stake_contract = web3.eth.contract(
        address=contracts["stake_contract_address"], abi=nulink_abi
    )

    get_rewards_pending = get_pending_user_reward(private_key)

    if get_rewards_pending > 1:

        nonce = web3.eth.get_transaction_count(sender_address)
        claim_tx = stake_contract.functions.claimReward(
            sender_address
        ).build_transaction(
            {
                "from": sender_address,
                "gas": 0,
                "nonce": nonce,
                "gasPrice": 0,
                "chainId": 97,
            }
        )
        signed_tx = sign_my_tx(claim_tx, private_key)
        if signed_tx is not None:
            try:
                tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                log.info(f"Transaction hash: {tx_hash.hex()}")
                return tx_hash.hex()
            except Exception as e:
                log.error(f"Transaction failed: {str(e)}")
                return False
        else:
            log.error(f"Transaction signing failed.")
            return False
    else:
        log.error(
            f"\033[93mWallet {sender_address} have only {get_rewards_pending} Nulink. Not need claim now\033[0m",
        )
        return False


def claim_rewards_wallets(file_manager):
    wallet_data = file_manager.get_all_wallet_data_from_file()

    for i, wallet in enumerate(wallet_data, start=1):

        checker_claim = claim_rewards(wallet["private_key"])
        if checker_claim:
            sleeping_time = random_time(10, 30)
            log.info(f"Wait {sleeping_time} second")
            time.sleep(sleeping_time)


def send_nulink(private_key_sender, address_to_send):
    with open("abi/contracts.json", mode="r", encoding="utf-8") as contracts_file:
        my_contracts = json.load(contracts_file)
    with open("abi/erc20.json", mode="r", encoding="utf-8") as erc20_abi_file:
        erc20_abi = json.load(erc20_abi_file)

    contract = web3.eth.contract(
        address=my_contracts["nulink_token_address"], abi=erc20_abi
    )
    sender_address = Web3.to_checksum_address(
        Account.from_key(private_key_sender).address
    )
    amount = get_token_balance(my_contracts["nulink_token_address"], sender_address)
    amount_nulink = amount / 10**18
    if amount > 0:
        transfer_tx = contract.functions.transfer(address_to_send, amount)(
            address_to_send, amount
        ).build_transaction(
            {
                "from": sender_address,
                "gas": 0,
                "gasPrice": 0,
                "nonce": web3.eth.get_transaction_count(sender_address),
                "chainId": 97,
            }
        )

        signed_tx = sign_my_tx(transfer_tx, private_key_sender)
        if signed_tx is not None:
            try:
                tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                log.info(f"Transaction hash: {tx_hash.hex()}")
                return True
            except Exception as e:
                log.error(f"Transaction failed: {str(e)}")
                return False
        else:
            log.error("Transaction signing failed.")
            return False
    else:
        log.info(f"\033[91mAmount: {amount_nulink} NLK. Cannot send it\033[0m")


def send_nulink_to_wallets(file_manager, nulink_manager):
    wallet_new_data = file_manager.get_all_wallet_data_from_file()
    wallet_nulink_data = nulink_manager.get_all_wallet_data_from_file()

    for i, (new_wallet, nulink_wallet) in enumerate(
        zip(wallet_new_data, wallet_nulink_data), start=1
    ):
        nulink_wallet_node = Web3.to_checksum_address(
            Account.from_key(nulink_wallet["private_key"]).address
        )
        new_wallet_bnb = Web3.to_checksum_address(
            Account.from_key(nulink_wallet["private_key"]).address
        )

        log.info(f"{i}.Try send from {new_wallet_bnb} to {nulink_wallet_node} 10 NLK")

        send_checker = send_nulink(new_wallet["private_key"], nulink_wallet_node)
        if send_checker:
            sleeping_time = random_time(25, 65)
            log.info(f"Wait {sleeping_time} second")
            time.sleep(sleeping_time)


def approve_token_spending(private_key):
    with open("abi/contracts.json", mode="r", encoding="utf-8") as contracts_file:
        my_contracts = json.load(contracts_file)
    with open("abi/erc20.json", mode="r", encoding="utf-8") as erc20_abi_file:
        erc20_abi = json.load(erc20_abi_file)

    spender_address = my_contracts["stake_contract_address"]
    sender_address = Web3.to_checksum_address(Account.from_key(private_key).address)
    contract = web3.eth.contract(
        address=my_contracts["nulink_token_address"], abi=erc20_abi
    )

    allowance_amount = contract.functions.allowance(
        sender_address,
        spender_address,
    ).call()

    amount = get_token_balance(my_contracts["nulink_token_address"], sender_address)

    if allowance_amount < amount:
        nonce = web3.eth.get_transaction_count(sender_address)
        approve_tx = contract.functions.approve(
            spender_address, 2**256 - 1
        ).build_transaction(
            {
                "from": sender_address,
                "gas": 0,
                "nonce": nonce,
                "gasPrice": 0,
                "chainId": 97,
            }
        )
        signed_tx = sign_my_tx(approve_tx, private_key)
        if signed_tx is not None:
            try:
                tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                log.info(f"Transaction hash approve: {tx_hash.hex()}")
                return True
            except Exception as e:
                log.error(f"Transaction failed: {str(e)}")
                return False
        else:
            log.error(f"Transaction signing failed.")
            return False
    else:
        return True


def display_menu():
    log.info("1. Create wallets")
    log.info("2. Delete new wallets")
    log.info("3. Send BNB to new wallets from main")
    log.info("4. Claim tokens Nulink from faucet (1 time)")
    log.info("5. Rewards Node Checker")
    log.info("6. Stake Nulink")
    log.info("7. Claim rewards Node")
    log.info("8. Send NLK tokens to Node Wallets")
    log.info("\033[31m10. Exit\033[0m")


def execute_option(choice, options):
    if choice in options:
        options[choice]()
        if choice == "10":
            return False
    else:
        log.error("Invalid choice. Please enter a valid option.")
    return True


def main():
    file_paths = {
        "ethereum_wallet": "config/ethereum_wallet.txt",
        "private_nulink": "config/private_nulink.txt",
        "private_main": "config/private_main.txt",
    }
    file_manager = FileManager(file_paths["ethereum_wallet"])
    nulink_manager = FileManager(file_paths["private_nulink"])

    private_key_main = FileManager(
        file_paths["private_main"]
    ).get_all_wallet_data_from_file()

    if private_key_main:
        private_key_main = random.choice(private_key_main)["private_key"]
    else:
        log.error("Please add main wallet private key")

    options = {
        "1": lambda: create_wallets(file_manager),
        "2": lambda: delete_wallets(file_manager),
        "3": lambda: send_bnb_to_wallets(file_manager, private_key_main),
        "4": lambda: claim_faucet_to_wallets(file_manager),
        "5": lambda: get_pending_user_reward_wallets(nulink_manager),
        "6": lambda: stake_wallets(nulink_manager),
        "7": lambda: claim_rewards_wallets(nulink_manager),
        "8": lambda: send_nulink_to_wallets(file_manager, nulink_manager),
        "10": lambda: log.info("\033[31mExiting...\033[0m"),
    }
    while True:
        display_menu()
        choice = input("Enter your choice: ")
        if not execute_option(choice, options):
            break


if __name__ == "__main__":
    main()
