import logging

from web3.exceptions import Web3RPCError

from modules.normalize import normalize_rpc_data
from modules.validation import validate_32byte_hash


logger = logging.getLogger(__name__)


def generate_trace_data(
    w3,
    tx_hash,
    options=None,
):
    logger.info("Collecting transaction trace")

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

    params = [tx_hash]

    if options is not None:
        params.append(options)

    logger.debug(
        "Requesting transaction trace: hash=%s",
        tx_hash,
    )

    try:
        response = w3.provider.make_request(
            "debug_traceTransaction",
            params,
        )

    except Exception as exc:
        logger.error(
            "Failed to retrieve transaction trace"
        )
        logger.debug(
            "Trace request exception: %s",
            type(exc).__name__,
        )
        raise

    if "error" in response:
        error = response["error"]

        if isinstance(error, dict):
            message = error.get(
                "message",
                "Unknown JSON-RPC error",
            )
        else:
            message = str(error)

        logger.error(
            "Trace RPC request failed: %s",
            message,
        )
        logger.debug(
            "Trace RPC error response: %s",
            normalize_rpc_data(error),
        )

        raise Web3RPCError(
            message,
            rpc_response=response,
        )

    if "result" not in response:
        logger.error(
            "Trace RPC response did not contain a result"
        )
        logger.debug(
            "Unexpected trace RPC response: %s",
            normalize_rpc_data(response),
        )

        raise Web3RPCError(
            "Trace RPC response did not contain a result",
            rpc_response=response,
        )

    trace_data = normalize_rpc_data(
        response["result"]
    )

    logger.debug(
        "Transaction trace collected successfully: hash=%s",
        tx_hash,
    )

    return trace_data
