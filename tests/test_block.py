import pytest
from web3.exceptions import BlockNotFound

from modules.block import generate_block_data
from modules.normalize import normalize_rpc_data

from conftest import UNKNOWN_HASH


def test_block_preserves_complete_rpc_response(
    w3,
    chain_state,
):
    block_number = chain_state["latest_block_number"]

    expected = normalize_rpc_data(
        w3.eth.get_block(block_number)
    )

    actual = generate_block_data(
        w3,
        block_number,
    )

    assert actual == expected


def test_block_preserves_canonical_field_names(
    w3,
    chain_state,
):
    data = generate_block_data(
        w3,
        chain_state["latest_block_number"],
    )

    assert "number" in data
    assert "parentHash" in data
    assert "transactions" in data

    assert "block" not in data
    assert "parent" not in data
    assert "transaction_count" not in data


def test_block_by_hash_preserves_complete_rpc_response(
    w3,
    chain_state,
):
    block_hash = chain_state["latest_block_hash"]

    expected = normalize_rpc_data(
        w3.eth.get_block(block_hash)
    )

    actual = generate_block_data(
        w3,
        block_hash,
    )

    assert actual == expected


def test_block_full_transactions_preserves_complete_response(
    w3,
    chain_state,
):
    block_number = chain_state["latest_block_number"]

    expected = normalize_rpc_data(
        w3.eth.get_block(
            block_number,
            full_transactions=True,
        )
    )

    actual = generate_block_data(
        w3,
        block_number,
        full_transactions=True,
    )

    assert actual == expected


def test_block_full_transactions_returns_transaction_objects(
    w3,
    chain_state,
):
    data = generate_block_data(
        w3,
        chain_state["latest_block_number"],
        full_transactions=True,
    )

    if data["transactions"]:
        assert isinstance(
            data["transactions"][0],
            dict,
        )


def test_block_not_found_raises(w3):
    with pytest.raises(BlockNotFound):
        generate_block_data(
            w3,
            UNKNOWN_HASH,
        )
