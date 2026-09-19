from web3 import Web3
import pytest

from modules.address import generate_address_data

from conftest import (
    ACCOUNT_1,
    ZERO_ADDRESS,
)


def test_address_data_matches_rpc_observations(w3):
    address = ACCOUNT_1.lower()
    rpc_address = Web3.to_checksum_address(address)

    expected = {
        "address": address,
        "balance": w3.eth.get_balance(
            rpc_address,
            "latest",
        ),
        "transaction_count": w3.eth.get_transaction_count(
            rpc_address,
            "latest",
        ),
        "code": w3.to_hex(
            w3.eth.get_code(
                rpc_address,
                "latest",
            )
        ),
    }

    actual = generate_address_data(
        w3,
        address,
    )

    assert actual == expected


def test_address_preserves_input_representation(w3):
    address = ACCOUNT_1.lower()

    data = generate_address_data(
        w3,
        address,
    )

    assert data["address"] == address


def test_address_contains_only_observed_fields(w3):
    data = generate_address_data(
        w3,
        ACCOUNT_1,
    )

    assert set(data) == {
        "address",
        "balance",
        "transaction_count",
        "code",
    }

    assert "account_type" not in data
    assert "code_size" not in data
    assert "nonce" not in data


def test_contract_code_is_preserved(
    w3,
    chain_state,
):
    address = chain_state["log_contract"]

    data = generate_address_data(
        w3,
        address,
    )

    expected_code = w3.to_hex(
        w3.eth.get_code(
            Web3.to_checksum_address(address),
            "latest",
        )
    )

    assert data["code"] == expected_code
    assert data["code"] != "0x"


def test_zero_address_preserves_rpc_state(w3):
    data = generate_address_data(
        w3,
        ZERO_ADDRESS,
    )

    rpc_address = Web3.to_checksum_address(
        ZERO_ADDRESS
    )

    assert data["balance"] == w3.eth.get_balance(
        rpc_address,
        "latest",
    )

    assert data["transaction_count"] == (
        w3.eth.get_transaction_count(
            rpc_address,
            "latest",
        )
    )

    assert data["code"] == w3.to_hex(
        w3.eth.get_code(
            rpc_address,
            "latest",
        )
    )


def test_address_respects_block_identifier(
    w3,
    chain_state,
):
    block_number = chain_state["latest_block_number"]
    address = ACCOUNT_1

    data = generate_address_data(
        w3,
        address,
        block_identifier=block_number,
    )

    rpc_address = Web3.to_checksum_address(address)

    assert data["balance"] == w3.eth.get_balance(
        rpc_address,
        block_number,
    )

    assert data["transaction_count"] == (
        w3.eth.get_transaction_count(
            rpc_address,
            block_number,
        )
    )

    assert data["code"] == w3.to_hex(
        w3.eth.get_code(
            rpc_address,
            block_number,
        )
    )


def test_address_invalid_input_raises(w3):
    with pytest.raises(
        ValueError,
        match="Address must be a valid 20-byte Ethereum address",
    ):
        generate_address_data(
            w3,
            "0x1234",
        )
