import logging

from web3.exceptions import TransactionNotFound

from modules.normalize import normalize_rpc_data
from modules.utils import validate_32byte_hash


logger = logging.getLogger(__name__)


def generate_transaction_data(w3, tx_hash):
    logger.info("Collecting transaction data")

    try:
        tx_hash = validate_32byte_hash(
            tx_hash,
            "transaction hash",
        )

    except ValueError as exc:
        logger.error(
            "Invalid transaction hash: %s",
            exc,
        )
        logger.debug(
            "Transaction hash validation exception: %s",
            type(exc).__name__,
        )
        raise

    logger.debug(
        "Requesting transaction: hash=%s",
        tx_hash,
    )

    try:
        transaction = w3.eth.get_transaction(tx_hash)

    except TransactionNotFound as exc:
        logger.error(
            "No transaction found for hash: %s",
            tx_hash,
        )
        logger.debug(
            "Transaction lookup exception: %s",
            type(exc).__name__,
        )
        raise

    except Exception as exc:
        logger.error(
            "Failed to retrieve transaction data"
        )
        logger.debug(
            "Transaction data exception: %s",
            type(exc).__name__,
        )
        raise

    transaction_data = normalize_rpc_data(transaction)

    logger.debug(
        "Transaction data collected successfully: "
        "hash=%s blockNumber=%s",
        transaction_data.get("hash"),
        transaction_data.get("blockNumber"),
    )

    return transaction_data
