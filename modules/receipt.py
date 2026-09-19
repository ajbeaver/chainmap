import logging

from web3.exceptions import TransactionNotFound

from modules.normalize import normalize_rpc_data
from modules.utils import validate_32byte_hash


logger = logging.getLogger(__name__)


def generate_receipt_data(w3, tx_hash):
    logger.info("Collecting receipt data")

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
        "Requesting receipt: transactionHash=%s",
        tx_hash,
    )

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)

    except TransactionNotFound as exc:
        logger.error(
            "No receipt found for transaction hash: %s",
            tx_hash,
        )
        logger.debug(
            "Receipt lookup exception: %s",
            type(exc).__name__,
        )
        raise

    except Exception as exc:
        logger.error(
            "Failed to retrieve receipt data"
        )
        logger.debug(
            "Receipt data exception: %s",
            type(exc).__name__,
        )
        raise

    receipt_data = normalize_rpc_data(receipt)

    logger.debug(
        "Receipt data collected successfully: "
        "transactionHash=%s blockNumber=%s",
        receipt_data.get("transactionHash"),
        receipt_data.get("blockNumber"),
    )

    return receipt_data
