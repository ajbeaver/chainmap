import pytest
from requests.exceptions import ConnectionError

from modules.rpc import (
    connect_rpc,
    sanitize_rpc_error_message,
    sanitize_rpc_url,
    validate_rpc_url,
)


@pytest.mark.parametrize(
    "rpc_url",
    [
        "http://127.0.0.1:8545",
        "https://example.com",
        "https://example.com/v3/api-key",
        "https://example.com/rpc?key=secret",
    ],
)
def test_validate_rpc_url_returns_valid_input(rpc_url):
    result = validate_rpc_url(rpc_url)

    assert result == rpc_url


@pytest.mark.parametrize(
    ("rpc_url", "message"),
    [
        (
            "ftp://127.0.0.1:8545",
            "RPC URL must use http or https",
        ),
        (
            "http:///missing-host",
            "RPC URL must include a hostname",
        ),
        (
            "http://127.0.0.1:notaport",
            "RPC URL contains an invalid port",
        ),
        (
            "http://[::1",
            "Invalid RPC URL",
        ),
    ],
)
def test_validate_rpc_url_rejects_invalid_input(
    rpc_url,
    message,
):
    with pytest.raises(ValueError, match=message):
        validate_rpc_url(rpc_url)


def test_connect_rpc_returns_working_web3(anvil_url):
    w3 = connect_rpc(anvil_url)

    assert w3.client_version
    assert w3.eth.chain_id == 31337


def test_connect_rpc_raises_for_unreachable_endpoint():
    rpc_url = "http://127.0.0.1:1"

    with pytest.raises(ConnectionError):
        connect_rpc(rpc_url)


def test_sanitize_rpc_url_preserves_local_endpoint():
    rpc_url = "http://127.0.0.1:8545"

    result = sanitize_rpc_url(rpc_url)

    assert result == rpc_url

def test_sanitize_rpc_url_redacts_local_credentials():
    rpc_url = (
        "http://user:secret@127.0.0.1:8545"
    )

    result = sanitize_rpc_url(rpc_url)

    assert result == (
        "http://127.0.0.1:8545/[REDACTED]"
    )

    assert "user" not in result
    assert "secret" not in result

def test_sanitize_rpc_url_redacts_remote_path():
    rpc_url = (
        "https://mainnet.example.com/api/super-secret-key"
    )

    result = sanitize_rpc_url(rpc_url)

    assert result == (
        "https://mainnet.example.com/[REDACTED]"
    )

    assert "super-secret-key" not in result


def test_sanitize_rpc_url_redacts_remote_query():
    rpc_url = (
        "https://mainnet.example.com/"
        "?api_key=super-secret-key"
    )

    result = sanitize_rpc_url(rpc_url)

    assert result == (
        "https://mainnet.example.com/[REDACTED]"
    )

    assert "super-secret-key" not in result


def test_sanitize_rpc_error_message_removes_secret_url():
    rpc_url = (
        "https://mainnet.example.com/api/super-secret-key"
    )

    exc = ConnectionError(
        f"Failed to connect to {rpc_url}"
    )

    result = sanitize_rpc_error_message(
        exc,
        rpc_url,
    )

    assert "super-secret-key" not in result
    assert (
        "https://mainnet.example.com/[REDACTED]"
        in result
    )
