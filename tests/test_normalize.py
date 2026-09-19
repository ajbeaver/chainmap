from modules.normalize import normalize_rpc_data


def test_normalize_bytes():
    value = bytes.fromhex("abcd")

    result = normalize_rpc_data(value)

    assert result == "0xabcd"


def test_normalize_bytearray():
    value = bytearray.fromhex("1234")

    result = normalize_rpc_data(value)

    assert result == "0x1234"


def test_normalize_mapping_recursively():
    value = {
        "hash": bytes.fromhex("11" * 32),
        "nested": {
            "data": bytearray.fromhex("abcd"),
        },
    }

    result = normalize_rpc_data(value)

    assert result == {
        "hash": "0x" + "11" * 32,
        "nested": {
            "data": "0xabcd",
        },
    }


def test_normalize_sequence_recursively():
    value = (
        bytes.fromhex("01"),
        {
            "value": bytearray.fromhex("02"),
        },
        7,
        None,
    )

    result = normalize_rpc_data(value)

    assert result == [
        "0x01",
        {
            "value": "0x02",
        },
        7,
        None,
    ]


def test_normalize_leaves_primitives_unchanged():
    values = [
        123,
        "hello",
        True,
        False,
        None,
    ]

    for value in values:
        assert normalize_rpc_data(value) == value
