import sys
import logging
from web3.exceptions import TransactionNotFound
from modules.utils import validate_32byte_hash

logger = logging.getLogger(__name__)

def generate_transaction_data(w3, tx_hash):
    logger.info("Collecting transaction data")

    try:
        tx_hash = validate_32byte_hash(tx_hash, "transaction hash")

    except ValueError as exc:
        logger.error("Invalid transaction hash: %s", exc)
        logger.debug("Transaction hash validation exception", exc_info=True)
        sys.exit(1)

    try:
        tx = w3.eth.get_transaction(tx_hash)
        logger.debug("Transaction data collected Successfully: %s", tx)

    except TransactionNotFound as exc:
        logger.error("No transaction found for hash: %s", tx_hash)
        logger.debug("Transaction lookup exception", exc_info=True)
        sys.exit(1)
        
    except Exception as exc:
        logger.error("Failed to retrieve transaction data: %s", exc)
        logger.debug("Transaction data exception", exc_info=True)
        sys.exit(1)
    
    
    transaction_data = {
        "hash": w3.to_hex(tx["hash"]),
        "block_hash": (
            w3.to_hex(tx["blockHash"])
            if tx["blockHash"] is not None
            else None
        ),
        "block_number": tx["blockNumber"],
        "transaction_index": tx["transactionIndex"],
        "from": tx["from"],
        "to": tx["to"],
        "value": tx["value"],
        "nonce": tx["nonce"],
        "input": w3.to_hex(tx["input"]),
        "gas": tx["gas"],
        "gas_price": tx.get("gasPrice"),
        "type": tx["type"],
        "v": tx.get("v"),
        "r": (
            w3.to_hex(tx["r"])
            if tx.get("r") is not None
            else None
        ),
        "s": (
            w3.to_hex(tx["s"])
            if tx.get("s") is not None
            else None
        ),
        "chain_id": tx.get("chainId"),
        "max_fee_per_gas": tx.get("maxFeePerGas"),
        "max_priority_fee_per_gas": tx.get("maxPriorityFeePerGas"),
        "access_list": tx.get("accessList"),
    }

    logger.debug("Transaction data generated successfully: %s", transaction_data)
    
    return transaction_data

def _format_transaction_data(w3, transaction_data):
    logger.info("Formatting transaction data for human readable output")
    formatted = transaction_data.copy()

    fee_fields = (
        "gas_price",
        "max_fee_per_gas",
        "max_priority_fee_per_gas",
    )

    for field in fee_fields:
        value = transaction_data.get(field)

        if value is not None:
            formatted[field] = f'{w3.from_wei(value, "gwei"):f} gwei'
        else:
            formatted[field] = "N/A"

    formatted["value"] = (
        f'{w3.from_wei(transaction_data["value"], "ether")} ETH'
    )
    
    formatted["gas"] = f'{transaction_data["gas"]:,}'
    
    block_number = transaction_data.get("block_number")

    if block_number is not None:
        formatted["block_number"] = f"{block_number:,}"
    else:
        formatted["block_number"] = "Pending"

    if transaction_data.get("block_hash") is None:
        formatted["block_hash"] = "Pending"

    if transaction_data.get("transaction_index") is None:
        formatted["transaction_index"] = "Pending"

    return formatted

def transaction_status(w3, tx_hash):
    transaction_data = generate_transaction_data(w3, tx_hash)
    return _format_transaction_data(w3, transaction_data)
