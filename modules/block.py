import sys
import logging
from datetime import datetime, timezone
from web3.exceptions import BlockNotFound

logger = logging.getLogger(__name__)

def _validate_block_identifier(block_id):
    if block_id == "latest":
        return block_id
    
    if isinstance(block_id, int):
        if block_id < 0:
            raise ValueError("Block number cannot be negative")
        return block_id
    
    if isinstance(block_id, str):
        try:
            block_number = int(block_id)
        except ValueError:
            block_number = None

        if block_number is not None:
            if block_number < 0:
                raise ValueError("Block number cannot be negative")

            return block_number

        if not block_id.startswith("0x"):
            raise ValueError(
                "Block hash must be a hexadecimal string starting with '0x'"
            )

        if len(block_id) != 66:
            raise ValueError("Block hash must be exactly 32 bytes")

        try:
            int(block_id[2:], 16)
        except ValueError:
            raise ValueError(
                "Block hash contains invalid hexadecimal characters"
            )

        return block_id

    raise ValueError("Unsupported block")

def generate_block_data(w3, block_id="latest"):
    logger.info("Collecting block data")

    try:
        block_id = _validate_block_identifier(block_id)
    
    except ValueError as exc:
        logger.error("Invalid block identifier: %s", exc)
        logger.debug("Block validation exception", exc_info=True)
        sys.exit(1)

    try:
        block = w3.eth.get_block(block_id)
        logger.debug("Block data collected successfully: %s", block)

    except BlockNotFound as exc:
        logger.error("No block found for identifier: %s", block_id)
        logger.debug("Block lookup exception", exc_info=True)
        sys.exit(1)

    except Exception as exc:
        logger.error("Failed to retrieve block data: %s", exc)
        logger.debug("Block data exception", exc_info=True)
        sys.exit(1)
        
    try:
        transaction_count = len(block["transactions"])
        logger.debug("Transaction cound collected successfully: %s", transaction_count)

    except Exception as exc:
        logger.error("Failed to retrieve transaction count: %s", exc)
        logger.debug("Transaction count exception", exc_info=True)
        sys.exit(1)

    block_data = {
        "block": block["number"],
        "hash": w3.to_hex(block["hash"]),
        "parent": w3.to_hex(block["parentHash"]),
        "timestamp": block["timestamp"],
        "transaction_count": transaction_count,
        "gas_used": block["gasUsed"],
        "gas_limit": block["gasLimit"],
        "base_fee": block.get("baseFeePerGas"),
        "fee_recipient": block["miner"],
    }

    logger.debug("Block data generated successfully: %s", block_data)

    return block_data

def _format_block_data(block_data):
    logger.info("Formatting block data for human readable output")
    formatted = block_data.copy()

    formatted["timestamp"] = datetime.fromtimestamp(
        block_data["timestamp"],
        tz=timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S UTC")

    formatted["transaction_count"] = f'{block_data["transaction_count"]:,}'
    formatted["gas_used"] = f'{block_data["gas_used"]:,}'
    formatted["gas_limit"] = f'{block_data["gas_limit"]:,}'

    if block_data["base_fee"] is not None:
        formatted["base_fee"] = f'{block_data["base_fee"]:,} wei'
    else:
        formatted["base_fee"] = "N/A"

    logger.debug("Formatted block data successfully: %s", formatted)

    return formatted

def block_status(w3, block_id="latest"):
    block_data = generate_block_data(w3, block_id)
    return _format_block_data(block_data)
