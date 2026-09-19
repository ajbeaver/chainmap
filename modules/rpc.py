import logging
from web3 import Web3
from urllib.parse import urlsplit
from requests.exceptions import ConnectionError, HTTPError, Timeout


logger = logging.getLogger(__name__)


def validate_rpc_url(rpc_url):
    try:
        parsed = urlsplit(rpc_url)

    except ValueError:
        raise ValueError("Invalid RPC URL")

    if parsed.scheme not in ("http", "https"):
        raise ValueError("RPC URL must use http or https")

    if not parsed.hostname:
        raise ValueError("RPC URL must include a hostname")

    try:
        parsed.port

    except ValueError:
        raise ValueError("RPC URL contains an invalid port")

    return rpc_url


def connect_rpc(provider):
    logger.info("Attempting connection to configured RPC")

    try:
        provider = validate_rpc_url(provider)

    except ValueError as exc:
        logger.error("Invalid RPC endpoint: %s", exc)
        logger.debug(
            "RPC validation exception: %s: %s",
            type(exc).__name__,
            exc,
        )
        raise

    logger.debug(
        "RPC endpoint validated successfully: %s",
        sanitize_rpc_url(provider),
    )

    safe_provider = sanitize_rpc_url(provider)

    w3 = Web3(Web3.HTTPProvider(provider))

    logger.debug("Web3 HTTP provider created successfully")

    try:
        client = w3.client_version

    except ConnectionError as exc:
        logger.error(
            "RPC endpoint is unreachable: %s",
            safe_provider,
        )
        logger.debug(
            "RPC connection exception: %s: %s",
            type(exc).__name__,
            sanitize_rpc_error_message(exc, provider),
        )
        raise

    except Timeout as exc:
        logger.error(
            "RPC endpoint timed out: %s",
            safe_provider,
        )
        logger.debug(
            "RPC timeout exception: %s: %s",
            type(exc).__name__,
            sanitize_rpc_error_message(exc, provider),
        )
        raise

    except HTTPError as exc:
        status = (
            exc.response.status_code
            if exc.response is not None
            else "unknown"
        )

        logger.error(
            "RPC endpoint responded but rejected the request: HTTP %s",
            status,
        )
        logger.debug(
            "RPC HTTP exception: %s: %s",
            type(exc).__name__,
            sanitize_rpc_error_message(exc, provider),
        )
        raise

    except Exception as exc:
        logger.error(
            "Endpoint responded but could not be validated as Ethereum JSON-RPC"
        )
        logger.debug(
            "RPC protocol exception: %s: %s",
            type(exc).__name__,
            sanitize_rpc_error_message(exc, provider),
        )
        raise

    logger.debug(
        "Successfully connected to Ethereum RPC: %s",
        client,
    )

    return w3


def sanitize_rpc_url(rpc_url):
    parsed = urlsplit(rpc_url)

    hostname = parsed.hostname or "unknown"

    has_sensitive_parts = (
        parsed.path not in ("", "/")
        or bool(parsed.query)
    )

    if (
        hostname in ("localhost", "127.0.0.1", "::1")
        and not has_sensitive_parts
    ):
        return rpc_url

    if parsed.port:
        hostname = f"{hostname}:{parsed.port}"

    return f"{parsed.scheme}://{hostname}/[REDACTED]"


def sanitize_rpc_error_message(exc, rpc_url):
    message = str(exc)
    parsed = urlsplit(rpc_url)

    message = message.replace(
        rpc_url,
        sanitize_rpc_url(rpc_url),
    )

    if parsed.path not in ("", "/"):
        message = message.replace(
            parsed.path,
            "/[REDACTED]",
        )

    if parsed.query:
        message = message.replace(
            parsed.query,
            "[REDACTED]",
        )

    return message
