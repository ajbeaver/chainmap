import logging
from collections.abc import Mapping

from web3.exceptions import BlockNotFound


logger = logging.getLogger(__name__)


def _normalize_rpc_data(value):
    if isinstance(value, (bytes, bytearray)):
        return "0x" + bytes(value).hex()

    if isinstance(value, Mapping):
        return {
            key: _normalize_rpc_data(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _normalize_rpc_data(item)
            for item in value
        ]

    return value


def generate_block_data(
    w3,
    block_id="latest",
    full_transactions=False,
):
    logger.info("Collecting block data")

    logger.debug(
        "Requesting block: identifier=%r full_transactions=%s",
        block_id,
        full_transactions,
    )

    try:
        block = w3.eth.get_block(
            block_id,
            full_transactions=full_transactions,
        )

    except BlockNotFound as exc:
        logger.error(
            "No block found for identifier: %s",
            block_id,
        )
        logger.debug(
            "Block lookup exception: %s",
            type(exc).__name__,
        )
        raise

    except Exception as exc:
        logger.error("Failed to retrieve block data")
        logger.debug(
            "Block data exception: %s",
            type(exc).__name__,
        )
        raise

    block_data = _normalize_rpc_data(block)

    logger.debug(
        "Block data collected successfully: number=%s hash=%s",
        block_data.get("number"),
        block_data.get("hash"),
    )

    return block_data
