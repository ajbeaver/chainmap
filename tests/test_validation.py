import pytest

from modules.validation import (
    validate_32byte_hash,
    validate_address,
)


VALID_HASH = "0x" + "11" * 32

VALID_LOWER_ADDRESS = (
    "0x70997970c51812dc3a010c7d01b50e0d17dc79c8"
)

VALID_UPPER_ADDRESS = (
    "0x70997970C51812DC3A010C7D01B50E0D17DC79C8"
)

VALID_CHECKSUM_ADDRESS = (
    "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
)


def test_validate_32byte_hash_returns_input():
    result = validate_32byte_hash(
        VALID_HASH,
        "transaction hash",
    )

    assert result == VALID_HASH


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (
            1234,
            "transaction hash must be a string",
        ),
        (
            "1234",
            "transaction hash must begin with 0x",
        ),
        (
            "0x1234",
            "transaction hash must be exactly 32 bytes",
        ),
        (
            "0x" + "zz" * 32,
            "transaction hash contains invalid hexadecimal characters",
        ),
    ],
)
def test_validate_32byte_hash_rejects_invalid_input(
    value,
    message,
):
    with pytest.raises(ValueError, match=message):
        validate_32byte_hash(
            value,
            "transaction hash",
        )


@pytest.mark.parametrize(
    "address",
    [
        VALID_LOWER_ADDRESS,
        VALID_UPPER_ADDRESS,
        VALID_CHECKSUM_ADDRESS,
    ],
)
def test_validate_address_returns_input_unchanged(address):
    result = validate_address(address)

    assert result == address


@pytest.mark.parametrize(
    ("address", "message"),
    [
        (
            1234,
            "Address must be a string",
        ),
        (
            "70997970C51812dc3A010C7d01b50e0d17dc79C8",
            "Address must begin with 0x",
        ),
        (
            "0x1234",
            "Address must be a valid 20-byte Ethereum address",
        ),
        (
            "0xzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
            "Address must be a valid 20-byte Ethereum address",
        ),
        (
            "0x70997970C51812dc3A010C7d01b50e0d17dc79C9",
            "Address has an invalid checksum",
        ),
    ],
)
def test_validate_address_rejects_invalid_input(
    address,
    message,
):
    with pytest.raises(ValueError, match=message):
        validate_address(address)
