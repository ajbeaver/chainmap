import sys
import logging
from web3 import Web3

logger = logging.getLogger(__name__)

def _validate_address(address):
    if not isinstance(address, str):
        raise ValueError("Address must be a string")

    if not address.startswith("0x"):
        raise ValueError("Address must begin with 0x")

    if not Web3.is_address(address):
        raise ValueError("Address must be a valid 20-byte Ethereum address")

    address_body = address[2:]

    is_lower = address_body == address_body.lower()
    is_upper = address_body == address_body.upper()

    if not is_lower and not is_upper:
        if not Web3.is_checksum_address(address):
            raise ValueError("Address has an invalid checksum")

    return Web3.to_checksum_address(address)

def generate_address_data(w3, acct_addr):
    logger.info("Collecting address data")

    try:
        address = _validate_address(acct_addr)

    except ValueError as exc:
        logger.error("Invalid Ethereum address: %s", exc)
        logger.debug("Address validation exception", exc_info=True)
        sys.exit(1)

    try:
        balance = w3.eth.get_balance(address)
        logger.debug("Address balance collected successfully: %s", balance)

    except Exception as exc:
        logger.error("Failed to retrieve address balance: %s", exc)
        logger.debug("Address balance exception", exc_info=True)
        sys.exit(1)

    try:
        nonce = w3.eth.get_transaction_count(address)
        logger.debug("Address nonce collected successfully: %s", nonce)

    except Exception as exc:
        logger.error("Failed to retreive address nonce: %s", exc)
        logger.debug("Address nonce exception", exc_info=True)
        sys.exit(1)

    try:
        code = w3.eth.get_code(address)
        logger.debug("Address code collected successfully: %s", code)

    except Exception as exc:
        logger.error("Failed to retreive address code: %s", exc)
        logger.debug("Address code exception", exc_info=True)
        sys.exit(1)

    account_type = "Contract" if len(code) > 0 else "EOA / No Code"
    
    address_data = {
        "address": address,
        "balance": balance,
        "nonce": nonce,
        "code": w3.to_hex(code),
        "account_type": account_type
    }

    logger.debug("Address data generated successfully: %s", address_data)

    return address_data

def _format_address_data(w3, address_data):
    logger.info("Formatting address data for human readable output")
    formatted = address_data.copy()

    formatted["balance"] = f'{w3.from_wei(address_data["balance"], "ether"):f} ETH'
    formatted["nonce"] = f'{address_data["nonce"]:,}'
    code = address_data.get("code", "0x")
    code_size = (len(code) - 2) // 2

    formatted["code_size"] = f"{code_size:,} bytes"
    formatted.pop("code", None)

    return formatted

def address_status(w3, acct_addr):
    address_data = generate_address_data(w3, acct_addr)
    return _format_address_data(w3, address_data)

    
