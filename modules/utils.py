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
        raise ValueError(f"{label} contains invalid hexadecimal characters")

    return value