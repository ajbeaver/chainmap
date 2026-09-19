from collections.abc import Mapping


def normalize_rpc_data(value):
    if isinstance(value, (bytes, bytearray)):
        return "0x" + bytes(value).hex()

    if isinstance(value, Mapping):
        return {
            key: normalize_rpc_data(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            normalize_rpc_data(item)
            for item in value
        ]

    return value
