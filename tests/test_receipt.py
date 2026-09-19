import pytest
from web3.exceptions import TransactionNotFound

from modules.normalize import normalize_rpc_data
from modules.receipt import generate_receipt_data

from conftest import UNKNOWN_HASH


@pytest.mark.parametrize(
    "key",
    [
        "legacy_tx_hash",
        "eip1559_tx_hash",
        "log_tx_hash",
        "deploy_log_tx_hash",
    ],
)
def test_receipt_preserves_complete_rpc_response(
    w3,
    chain_state,
    key,
):
    tx_hash = chain_state[key]

    expected = normalize_rpc_data(
        w3.eth.get_transaction_receipt(tx_hash)
    )

    actual = generate_receipt_data(
        w3,
        tx_hash,
    )

    assert actual == expected


def test_receipt_preserves_canonical_field_names(
    w3,
    chain_state,
):
    data = generate_receipt_data(
        w3,
        chain_state["legacy_tx_hash"],
    )

    assert "transactionHash" in data
    assert "transactionIndex" in data
    assert "blockHash" in data
    assert "blockNumber" in data
    assert "gasUsed" in data
    assert "cumulativeGasUsed" in data

    assert "transaction_hash" not in data
    assert "transaction_index" not in data
    assert "block_hash" not in data
    assert "block_number" not in data
    assert "gas_used" not in data


def test_receipt_preserves_logs(
    w3,
    chain_state,
):
    data = generate_receipt_data(
        w3,
        chain_state["log_tx_hash"],
    )

    assert "logs" in data
    assert len(data["logs"]) == 1

    log = data["logs"][0]

    assert isinstance(log, dict)
    assert "address" in log
    assert "topics" in log
    assert "data" in log


def test_receipt_preserves_logs_bloom(
    w3,
    chain_state,
):
    data = generate_receipt_data(
        w3,
        chain_state["log_tx_hash"],
    )

    assert "logsBloom" in data
    assert isinstance(data["logsBloom"], str)
    assert data["logsBloom"].startswith("0x")


def test_contract_creation_receipt_preserves_contract_address(
    w3,
    chain_state,
):
    data = generate_receipt_data(
        w3,
        chain_state["deploy_log_tx_hash"],
    )

    assert data["contractAddress"] is not None
    assert (
        data["contractAddress"].lower()
        == chain_state["log_contract"].lower()
    )


def test_receipt_status_remains_raw_integer(
    w3,
    chain_state,
):
    data = generate_receipt_data(
        w3,
        chain_state["legacy_tx_hash"],
    )

    assert data["status"] == 1
    assert isinstance(data["status"], int)


def test_receipt_not_found_raises(w3):
    with pytest.raises(TransactionNotFound):
        generate_receipt_data(
            w3,
            UNKNOWN_HASH,
        )


def test_receipt_invalid_hash_raises(w3):
    with pytest.raises(
        ValueError,
        match="transaction hash must be exactly 32 bytes",
    ):
        generate_receipt_data(
            w3,
            "0x1234",
        )
