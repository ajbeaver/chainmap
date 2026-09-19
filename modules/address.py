import logging

from web3 import Web3

from modules.normalize import normalize_rpc_data
from modules.validation import validate_address


logger = logging.getLogger(__name__)


def generate_address_data(
    w3,
    address,
    block_identifier="latest",
):
    logger.info("Collecting address data")

    try:
        address = validate_address(address)

    except ValueError as exc:
        logger.error(
            "Invalid Ethereum address: %s",
            exc,
        )
        logger.debug(
            "Address validation exception: %s",
            type(exc).__name__,
        )
        raise

    rpc_address = Web3.to_checksum_address(address)

    logger.debug(
        "Requesting address state: address=%s block=%r",
        rpc_address,
        block_identifier,
    )

    try:
        balance = w3.eth.get_balance(
            rpc_address,
            block_identifier,
        )

        logger.debug(
            "Address balance collected successfully: %s",
            balance,
        )

    except Exception as exc:
        logger.error(
            "Failed to retrieve address balance"
        )
        logger.debug(
            "Address balance exception: %s",
            type(exc).__name__,
        )
        raise

    try:
        transaction_count = w3.eth.get_transaction_count(
            rpc_address,
            block_identifier,
        )

        logger.debug(
            "Address transaction count collected successfully: %s",
            transaction_count,
        )

    except Exception as exc:
        logger.error(
            "Failed to retrieve address transaction count"
        )
        logger.debug(
            "Address transaction count exception: %s",
            type(exc).__name__,
        )
        raise

    try:
        code = w3.eth.get_code(
            rpc_address,
            block_identifier,
        )

        logger.debug(
            "Address code collected successfully"
        )

    except Exception as exc:
        logger.error(
            "Failed to retrieve address code"
        )
        logger.debug(
            "Address code exception: %s",
            type(exc).__name__,
        )
        raise

    address_data = normalize_rpc_data({
        "address": address,
        "balance": balance,
        "transaction_count": transaction_count,
        "code": code,
    })

    logger.debug(
        "Address data collected successfully: "
        "address=%s block=%r",
        address,
        block_identifier,
    )

    return address_data
