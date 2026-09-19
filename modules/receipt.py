import sys
import logging
from web3.exceptions import TransactionNotFound
from modules.utils import validate_32byte_hash

logger = logging.getLogger(__name__)

def generate_receipt_data(w3, tx_hash):
    logger.info("Collecting receipt data")

    try:
        tx_hash = validate_32byte_hash(tx_hash, "transaction hash")

    except ValueError as exc:
        logger.error("Invalid transaction hash: %s", exc)
        logger.debug("Transaction hash validation exception", exc_info=True)
        sys.exit(1)

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        logger.debug("Receipt collected Successfully: %s", receipt)

    except TransactionNotFound as exc:
        logger.debug("Receipt not available for hash: %s", tx_hash)
        logger.debug("Receipt lookup exception", exc_info=True)

        try:
            w3.eth.get_transaction(tx_hash)

        except TransactionNotFound as tx_exc:
            logger.error("No transaction found for hash: %s", tx_hash)
            logger.debug("Transaction lookup exception", exc_info=True)
            sys.exit(1)

        return None

    except Exception as exc:
        logger.error("Failed to retrieve receipt data: %s", exc)
        logger.debug("Receipt data exception", exc_info=True)
        sys.exit(1)

    receipt_data = {
        "transaction_hash": w3.to_hex(receipt["transactionHash"]),
        "transaction_index": receipt["transactionIndex"],
        "block_hash": w3.to_hex(receipt["blockHash"]),
        "block_number": receipt["blockNumber"],
        "from": receipt["from"],
        "to": receipt["to"],
        "status": receipt["status"],
        "gas_used": receipt["gasUsed"],
        "cumulative_gas_used": receipt["cumulativeGasUsed"],
        "effective_gas_price": receipt.get("effectiveGasPrice"),
        "contract_address": receipt["contractAddress"],
        "logs": receipt["logs"],
        "logs_bloom": w3.to_hex(receipt["logsBloom"]),
        "type": receipt.get("type"),
    }

    logger.debug("Receipt data generated successfully: %s", receipt_data)

    return receipt_data
    
def _format_receipt_data(w3, receipt_data):
    logger.info("Formatting receipt data for human readable output")
    formatted = receipt_data.copy()

    formatted["status"] = (
        "Success"
        if receipt_data["status"] == 1
        else "Failed"
    )

    num_fields = (
        "gas_used",
        "cumulative_gas_used",
    )
    
    for field in num_fields:
        value = receipt_data.get(field)

        if value is not None:
            formatted[field] = f'{value:,}'
        else:
            formatted[field] = "N/A"

    effective_gas_price = receipt_data.get("effective_gas_price")

    if effective_gas_price is not None:
        formatted["effective_gas_price"] = (
            f'{w3.from_wei(effective_gas_price, "gwei"):f} gwei'
        )
    else:
        formatted["effective_gas_price"] = "N/A"

    logs = receipt_data.get("logs", [])
    formatted["log_count"] = len(logs)
    formatted.pop("logs", None)
    formatted.pop("logs_bloom", None)

    logger.debug("Formatted receipt data successfully: %s", formatted)

    return formatted

def receipt_status(w3, tx_hash):
    receipt_data = generate_receipt_data(w3, tx_hash)

    if receipt_data is None:
        return None

    return _format_receipt_data(w3, receipt_data)
