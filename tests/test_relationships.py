import copy

import pytest

from modules.execution import extract_execution_frames
from modules.relationships import extract_relationships
from modules.trace import generate_trace_data


TX_HASH = "0x" + "11" * 32


def build_execution_records():
    return [
        {
            "transaction_hash": TX_HASH,
            "frame_path": [0],
            "frame": {
                "type": "CALL",
                "from": "0xAaA",
                "to": "0xBbB",
                "value": "0x0",
                "customField": "preserve-me",
            },
        },
        {
            "transaction_hash": TX_HASH,
            "frame_path": [0, 0],
            "frame": {
                "type": "DELEGATECALL",
                "from": "0xBbB",
                "to": "0xCcC",
                "gas": "0x1234",
            },
        },
        {
            "transaction_hash": TX_HASH,
            "frame_path": [0, 1],
            "frame": {
                "type": "CALL",
                "from": "0xBbB",
                "to": "0xDdD",
                "error": "execution reverted",
                "revertReason": "test failure",
            },
        },
    ]


def test_relationships_preserve_order():
    execution_records = build_execution_records()

    relationships = extract_relationships(
        execution_records
    )

    assert [
        relationship["frame_path"]
        for relationship in relationships
    ] == [
        [0],
        [0, 0],
        [0, 1],
    ]


def test_relationship_preserves_promoted_fields():
    execution_records = build_execution_records()

    relationships = extract_relationships(
        execution_records
    )

    relationship = relationships[0]

    assert relationship["from"] == "0xAaA"
    assert relationship["to"] == "0xBbB"
    assert relationship["type"] == "CALL"
    assert relationship["transaction_hash"] == TX_HASH
    assert relationship["frame_path"] == [0]


def test_relationship_preserves_complete_evidence():
    execution_records = build_execution_records()

    relationships = extract_relationships(
        execution_records
    )

    assert relationships[0]["evidence"] == {
        "type": "CALL",
        "from": "0xAaA",
        "to": "0xBbB",
        "value": "0x0",
        "customField": "preserve-me",
    }


def test_relationship_preserves_address_representation():
    execution_records = build_execution_records()

    relationships = extract_relationships(
        execution_records
    )

    assert relationships[0]["from"] == "0xAaA"
    assert relationships[0]["to"] == "0xBbB"


def test_relationship_preserves_unknown_type():
    execution_records = [
        {
            "transaction_hash": TX_HASH,
            "frame_path": [0],
            "frame": {
                "type": "FUTURE_CALL_TYPE",
                "from": "0xaaa",
                "to": "0xbbb",
            },
        },
    ]

    relationships = extract_relationships(
        execution_records
    )

    assert len(relationships) == 1
    assert (
        relationships[0]["type"]
        == "FUTURE_CALL_TYPE"
    )


def test_relationship_preserves_failed_calls():
    execution_records = build_execution_records()

    relationships = extract_relationships(
        execution_records
    )

    failed = relationships[2]

    assert failed["from"] == "0xBbB"
    assert failed["to"] == "0xDdD"
    assert (
        failed["evidence"]["error"]
        == "execution reverted"
    )
    assert (
        failed["evidence"]["revertReason"]
        == "test failure"
    )


def test_relationships_do_not_deduplicate():
    execution_records = [
        {
            "transaction_hash": TX_HASH,
            "frame_path": [0, 0],
            "frame": {
                "type": "CALL",
                "from": "0xaaa",
                "to": "0xbbb",
            },
        },
        {
            "transaction_hash": TX_HASH,
            "frame_path": [0, 1],
            "frame": {
                "type": "CALL",
                "from": "0xaaa",
                "to": "0xbbb",
            },
        },
    ]

    relationships = extract_relationships(
        execution_records
    )

    assert len(relationships) == 2

    assert (
        relationships[0]["from"]
        == relationships[1]["from"]
    )
    assert (
        relationships[0]["to"]
        == relationships[1]["to"]
    )
    assert (
        relationships[0]["type"]
        == relationships[1]["type"]
    )

    assert relationships[0]["frame_path"] == [0, 0]
    assert relationships[1]["frame_path"] == [0, 1]


def test_relationships_skip_frame_without_from():
    execution_records = [
        {
            "transaction_hash": TX_HASH,
            "frame_path": [0],
            "frame": {
                "type": "CALL",
                "to": "0xbbb",
            },
        },
    ]

    relationships = extract_relationships(
        execution_records
    )

    assert relationships == []


def test_relationships_skip_frame_without_to():
    execution_records = [
        {
            "transaction_hash": TX_HASH,
            "frame_path": [0],
            "frame": {
                "type": "CALL",
                "from": "0xaaa",
            },
        },
    ]

    relationships = extract_relationships(
        execution_records
    )

    assert relationships == []


@pytest.mark.parametrize(
    "frame",
    [
        {
            "type": "CALL",
            "from": None,
            "to": "0xbbb",
        },
        {
            "type": "CALL",
            "from": "0xaaa",
            "to": None,
        },
    ],
)
def test_relationships_skip_null_endpoints(frame):
    execution_records = [
        {
            "transaction_hash": TX_HASH,
            "frame_path": [0],
            "frame": frame,
        },
    ]

    relationships = extract_relationships(
        execution_records
    )

    assert relationships == []


def test_relationships_empty_input_returns_empty_list():
    assert extract_relationships([]) == []


def test_relationships_do_not_mutate_input():
    execution_records = build_execution_records()
    original = copy.deepcopy(execution_records)

    extract_relationships(
        execution_records
    )

    assert execution_records == original


def test_relationship_output_does_not_alias_source():
    execution_records = build_execution_records()

    relationships = extract_relationships(
        execution_records
    )

    relationships[0]["frame_path"].append(99)
    relationships[0]["evidence"][
        "customField"
    ] = "changed"

    assert (
        execution_records[0]["frame_path"]
        == [0]
    )

    assert (
        execution_records[0]["frame"][
            "customField"
        ]
        == "preserve-me"
    )


def test_relationships_reject_non_list_input():
    with pytest.raises(
        ValueError,
        match="Execution records must be a list",
    ):
        extract_relationships({})


def test_relationships_reject_non_mapping_record():
    with pytest.raises(
        ValueError,
        match="Execution record must be a mapping",
    ):
        extract_relationships(
            [
                "not-a-record",
            ]
        )


@pytest.mark.parametrize(
    ("record", "message"),
    [
        (
            {
                "frame_path": [0],
                "frame": {
                    "type": "CALL",
                },
            },
            "Execution record must include transaction_hash",
        ),
        (
            {
                "transaction_hash": TX_HASH,
                "frame": {
                    "type": "CALL",
                },
            },
            "Execution record must include frame_path",
        ),
        (
            {
                "transaction_hash": TX_HASH,
                "frame_path": [0],
            },
            "Execution record must include frame",
        ),
    ],
)
def test_relationships_reject_missing_record_fields(
    record,
    message,
):
    with pytest.raises(
        ValueError,
        match=message,
    ):
        extract_relationships(
            [record]
        )


def test_relationships_reject_non_string_transaction_hash():
    execution_records = [
        {
            "transaction_hash": 1234,
            "frame_path": [0],
            "frame": {
                "type": "CALL",
            },
        },
    ]

    with pytest.raises(
        ValueError,
        match=(
            "Execution record transaction_hash "
            "must be a string"
        ),
    ):
        extract_relationships(
            execution_records
        )


def test_relationships_reject_non_list_frame_path():
    execution_records = [
        {
            "transaction_hash": TX_HASH,
            "frame_path": "0.1",
            "frame": {
                "type": "CALL",
            },
        },
    ]

    with pytest.raises(
        ValueError,
        match=(
            "Execution record frame_path "
            "must be a list"
        ),
    ):
        extract_relationships(
            execution_records
        )


def test_relationships_reject_empty_frame_path():
    execution_records = [
        {
            "transaction_hash": TX_HASH,
            "frame_path": [],
            "frame": {
                "type": "CALL",
            },
        },
    ]

    with pytest.raises(
        ValueError,
        match=(
            "Execution record frame_path "
            "must not be empty"
        ),
    ):
        extract_relationships(
            execution_records
        )


@pytest.mark.parametrize(
    "frame_path",
    [
        [0, -1],
        [0, "1"],
        [0, 1.5],
        [0, None],
    ],
)
def test_relationships_reject_invalid_frame_path_values(
    frame_path,
):
    execution_records = [
        {
            "transaction_hash": TX_HASH,
            "frame_path": frame_path,
            "frame": {
                "type": "CALL",
            },
        },
    ]

    with pytest.raises(
        ValueError,
        match=(
            "Execution record frame_path "
            "must contain non-negative integers"
        ),
    ):
        extract_relationships(
            execution_records
        )


def test_relationships_reject_non_mapping_frame():
    execution_records = [
        {
            "transaction_hash": TX_HASH,
            "frame_path": [0],
            "frame": [],
        },
    ]

    with pytest.raises(
        ValueError,
        match=(
            "Execution record frame "
            "must be a mapping"
        ),
    ):
        extract_relationships(
            execution_records
        )


def test_relationships_reject_missing_type():
    execution_records = [
        {
            "transaction_hash": TX_HASH,
            "frame_path": [0],
            "frame": {
                "from": "0xaaa",
                "to": "0xbbb",
            },
        },
    ]

    with pytest.raises(
        ValueError,
        match="Execution frame must include type",
    ):
        extract_relationships(
            execution_records
        )


def test_relationships_reject_null_type():
    execution_records = [
        {
            "transaction_hash": TX_HASH,
            "frame_path": [0],
            "frame": {
                "type": None,
                "from": "0xaaa",
                "to": "0xbbb",
            },
        },
    ]

    with pytest.raises(
        ValueError,
        match=(
            "Execution frame type must not be null"
        ),
    ):
        extract_relationships(
            execution_records
        )


def test_relationships_compose_with_execution_and_trace(
    w3,
    chain_state,
):
    tx_hash = chain_state[
        "nested_call_tx_hash"
    ]

    trace_data = generate_trace_data(
        w3,
        tx_hash,
        {
            "tracer": "callTracer",
        },
    )

    execution_records = extract_execution_frames(
        trace_data,
        tx_hash,
    )

    relationships = extract_relationships(
        execution_records
    )

    assert [
        relationship["frame_path"]
        for relationship in relationships
    ] == [
        [0],
        [0, 0],
        [0, 0, 0],
    ]

    root = relationships[0]
    first_call = relationships[1]
    second_call = relationships[2]

    assert (
        root["to"].lower()
        == chain_state["caller_contract"].lower()
    )

    assert (
        first_call["from"].lower()
        == chain_state["caller_contract"].lower()
    )

    assert (
        first_call["to"].lower()
        == chain_state["middle_contract"].lower()
    )

    assert (
        second_call["from"].lower()
        == chain_state["middle_contract"].lower()
    )

    assert (
        second_call["to"].lower()
        == chain_state["leaf_contract"].lower()
    )

    for relationship in relationships:
        assert (
            relationship["transaction_hash"]
            == tx_hash
        )

        assert (
            relationship["type"]
            == relationship["evidence"]["type"]
        )

        assert (
            relationship["from"]
            == relationship["evidence"]["from"]
        )

        assert (
            relationship["to"]
            == relationship["evidence"]["to"]
        )


def test_relationships_reject_boolean_frame_path_value():
    execution_records = [
        {
            "transaction_hash": TX_HASH,
            "frame_path": [0, True],
            "frame": {
                "type": "CALL",
            },
        },
    ]

    with pytest.raises(
        ValueError,
        match=(
            "Execution record frame_path "
            "must contain non-negative integers"
        ),
    ):
        extract_relationships(
            execution_records
        )
