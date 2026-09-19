import pytest
from web3.exceptions import TransactionNotFound

from modules.normalize import normalize_rpc_data
from modules.transaction import generate_transaction_data

from conftest import UNKNOWN_HASH


@pytest.mark.parametrize(
    "key",
    [
        "legacy_tx_hash",
        "eip1559_tx_hash",
    ],
)
def test_transaction_preserves_complete_rpc_response(
    w3,
    chain_state,
    key,
):
    tx_hash = chain_state[key]

    expected = normalize_rpc_data(
        w3.eth.get_transaction(tx_hash)
    )

    actual = generate_transaction_data(
        w3,
        tx_hash,
    )

    assert actual == expected


def test_transaction_preserves_canonical_field_names(
    w3,
    chain_state,
):
    data = generate_transaction_data(
        w3,
        chain_state["eip1559_tx_hash"],
    )

    assert "blockHash" in data
    assert "blockNumber" in data
    assert "transactionIndex" in data
    assert "gasPrice" in data
    assert "chainId" in data

    assert "block_hash" not in data
    assert "block_number" not in data
    assert "transaction_index" not in data
    assert "gas_price" not in data
    assert "chain_id" not in data


def test_eip1559_transaction_preserves_fee_fields(
    w3,
    chain_state,
):
    data = generate_transaction_data(
        w3,
        chain_state["eip1559_tx_hash"],
    )

    assert "maxFeePerGas" in data
    assert "maxPriorityFeePerGas" in data

    assert data["maxFeePerGas"] is not None
    assert data["maxPriorityFeePerGas"] is not None


def test_transaction_hash_is_normalized(
    w3,
    chain_state,
):
    data = generate_transaction_data(
        w3,
        chain_state["legacy_tx_hash"],
    )

    assert isinstance(data["hash"], str)
    assert data["hash"].startswith("0x")


def test_transaction_not_found_raises(w3):
    with pytest.raises(TransactionNotFound):
        generate_transaction_data(
            w3,
            UNKNOWN_HASH,
        )


def test_transaction_invalid_hash_raises(w3):
    with pytest.raises(
        ValueError,
        match="transaction hash must be exactly 32 bytes",
    ):
        generate_transaction_data(
            w3,
            "0x1234",
        )
