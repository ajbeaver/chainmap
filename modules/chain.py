import logging


logger = logging.getLogger(__name__)


def generate_chain_data(w3):
    logger.info("Collecting chain data")

    try:
        client = w3.client_version
        logger.debug(
            "Client version collected successfully: %s",
            client,
        )

    except Exception as exc:
        logger.error("Failed to retrieve client version")
        logger.debug(
            "Client version exception: %s",
            type(exc).__name__,
        )
        raise

    try:
        chain_id = w3.eth.chain_id
        logger.debug(
            "Chain ID collected successfully: %s",
            chain_id,
        )

    except Exception as exc:
        logger.error("Failed to retrieve chain ID")
        logger.debug(
            "Chain ID exception: %s",
            type(exc).__name__,
        )
        raise

    try:
        block_number = w3.eth.block_number
        logger.debug(
            "Block number collected successfully: %s",
            block_number,
        )

    except Exception as exc:
        logger.error("Failed to retrieve block number")
        logger.debug(
            "Block number exception: %s",
            type(exc).__name__,
        )
        raise

    try:
        syncing = w3.eth.syncing
        logger.debug(
            "Sync data collected successfully: %s",
            syncing,
        )

    except Exception as exc:
        logger.error("Failed to retrieve sync data")
        logger.debug(
            "Sync data exception: %s",
            type(exc).__name__,
        )
        raise

    chain_data = {
        "client": client,
        "chain_id": chain_id,
        "block_number": block_number,
        "syncing": syncing,
    }

    logger.debug(
        "Chain data generated successfully: %s",
        chain_data,
    )

    return chain_data
