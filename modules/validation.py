from web3 import Web3


def validate_32byte_hash(value, label="hash"):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")

    if not value.startswith("0x"):
        raise ValueError(f"{label} must begin with 0x")

    if len(value) != 66:
        raise ValueError(f"{label} must be exactly 32 bytes")

    try:
        int(value[2:], 16)

    except ValueError:
        raise ValueError(
            f"{label} contains invalid hexadecimal characters"
        )

    return value


def validate_address(address):
    if not isinstance(address, str):
        raise ValueError("Address must be a string")

    if not address.startswith("0x"):
        raise ValueError("Address must begin with 0x")

    if not Web3.is_address(address):
        raise ValueError(
            "Address must be a valid 20-byte Ethereum address"
        )

    address_body = address[2:]

    is_lower = address_body == address_body.lower()
    is_upper = address_body == address_body.upper()

    if not is_lower and not is_upper:
        if not Web3.is_checksum_address(address):
            raise ValueError(
                "Address has an invalid checksum"
            )

    return address
