import copy

import pytest

from modules.execution import extract_execution_frames
from modules.trace import generate_trace_data


TX_HASH = "0x" + "11" * 32


def build_trace_data():
    return {
        "type": "CALL",
        "from": "0xaaa",
        "to": "0xbbb",
        "value": "0x0",
        "customField": "preserve-me",
        "calls": [
            {
                "type": "CALL",
                "from": "0xbbb",
                "to": "0xccc",
                "value": "0x1",
                "calls": [
                    {
                        "type": "STATICCALL",
                        "from": "0xccc",
                        "to": "0xddd",
                        "gas": "0x1234",
                    },
                ],
            },
            {
                "type": "CALL",
                "from": "0xbbb",
                "to": "0xeee",
                "error": "execution reverted",
            },
        ],
    }


def test_execution_frames_preserve_order_and_paths():
    trace_data = build_trace_data()

    records = extract_execution_frames(
        trace_data,
        TX_HASH,
    )

    assert [
        record["frame_path"]
        for record in records
    ] == [
        [0],
        [0, 0],
        [0, 0, 0],
        [0, 1],
    ]


def test_execution_frame_preserves_local_fields():
    trace_data = build_trace_data()

    records = extract_execution_frames(
        trace_data,
        TX_HASH,
    )

    assert records[0]["frame"] == {
        "type": "CALL",
        "from": "0xaaa",
        "to": "0xbbb",
        "value": "0x0",
        "customField": "preserve-me",
    }

    assert records[2]["frame"] == {
        "type": "STATICCALL",
        "from": "0xccc",
        "to": "0xddd",
        "gas": "0x1234",
    }


def test_execution_frames_remove_only_nested_calls():
    trace_data = build_trace_data()

    records = extract_execution_frames(
        trace_data,
        TX_HASH,
    )

    for record in records:
        assert "calls" not in record["frame"]

    assert (
        records[0]["frame"]["customField"]
        == "preserve-me"
    )

    assert (
        records[3]["frame"]["error"]
        == "execution reverted"
    )


def test_execution_frames_preserve_failed_calls():
    trace_data = build_trace_data()

    records = extract_execution_frames(
        trace_data,
        TX_HASH,
    )

    failed_frame = records[3]

    assert failed_frame["frame_path"] == [0, 1]
    assert (
        failed_frame["frame"]["error"]
        == "execution reverted"
    )


def test_execution_frames_preserve_transaction_hash():
    trace_data = build_trace_data()

    records = extract_execution_frames(
        trace_data,
        TX_HASH,
    )

    for record in records:
        assert (
            record["transaction_hash"]
            == TX_HASH
        )


def test_execution_frames_do_not_mutate_input():
    trace_data = build_trace_data()
    original = copy.deepcopy(trace_data)

    extract_execution_frames(
        trace_data,
        TX_HASH,
    )

    assert trace_data == original
    assert "calls" in trace_data
    assert "calls" in trace_data["calls"][0]


def test_execution_frames_do_not_deduplicate_calls():
    trace_data = {
        "type": "CALL",
        "from": "0xaaa",
        "to": "0xbbb",
        "calls": [
            {
                "type": "CALL",
                "from": "0xbbb",
                "to": "0xccc",
            },
            {
                "type": "CALL",
                "from": "0xbbb",
                "to": "0xccc",
            },
        ],
    }

    records = extract_execution_frames(
        trace_data,
        TX_HASH,
    )

    assert len(records) == 3

    assert records[1]["frame"] == records[2]["frame"]

    assert records[1]["frame_path"] == [0, 0]
    assert records[2]["frame_path"] == [0, 1]


def test_execution_invalid_transaction_hash_raises():
    with pytest.raises(
        ValueError,
        match="transaction hash must be exactly 32 bytes",
    ):
        extract_execution_frames(
            build_trace_data(),
            "0x1234",
        )


def test_execution_rejects_non_mapping_trace():
    with pytest.raises(
        ValueError,
        match="Trace data must be a callTracer mapping",
    ):
        extract_execution_frames(
            [],
            TX_HASH,
        )


def test_execution_rejects_non_call_tracer_result():
    trace_data = {
        "failed": False,
        "gas": 21000,
        "returnValue": "0x",
        "structLogs": [],
    }

    with pytest.raises(
        ValueError,
        match="Trace data does not appear to be a callTracer result",
    ):
        extract_execution_frames(
            trace_data,
            TX_HASH,
        )


def test_execution_rejects_invalid_calls_structure():
    trace_data = {
        "type": "CALL",
        "from": "0xaaa",
        "to": "0xbbb",
        "calls": {},
    }

    with pytest.raises(
        ValueError,
        match="Execution frame calls must be a list",
    ):
        extract_execution_frames(
            trace_data,
            TX_HASH,
        )


def test_execution_rejects_non_mapping_child_frame():
    trace_data = {
        "type": "CALL",
        "from": "0xaaa",
        "to": "0xbbb",
        "calls": [
            "not-a-frame",
        ],
    }

    with pytest.raises(
        ValueError,
        match="Execution frame must be a mapping",
    ):
        extract_execution_frames(
            trace_data,
            TX_HASH,
        )


def test_execution_composes_with_real_call_trace(
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

    records = extract_execution_frames(
        trace_data,
        tx_hash,
    )

    assert [
        record["frame_path"]
        for record in records
    ] == [
        [0],
        [0, 0],
        [0, 0, 0],
    ]

    root = records[0]["frame"]
    first_call = records[1]["frame"]
    second_call = records[2]["frame"]

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


def test_execution_frames_do_not_alias_input():
    trace_data = {
        "type": "CALL",
        "from": "0xaaa",
        "to": "0xbbb",
        "logs": [
            {
                "address": "0xccc",
                "topics": [
                    "0x111",
                    "0x222",
                ],
                "data": "0x1234",
            }
        ],
        "customField": {
            "nested": [
                "preserve-me",
            ],
        },
    }

    records = extract_execution_frames(
        trace_data,
        TX_HASH,
    )

    frame = records[0]["frame"]

    frame["logs"][0]["data"] = "0xchanged"
    frame["logs"][0]["topics"].append(
        "0x333"
    )
    frame["customField"]["nested"].append(
        "changed"
    )

    assert trace_data["logs"] == [
        {
            "address": "0xccc",
            "topics": [
                "0x111",
                "0x222",
            ],
            "data": "0x1234",
        }
    ]

    assert trace_data["customField"] == {
        "nested": [
            "preserve-me",
        ],
    }


def test_execution_frames_are_isolated_from_later_input_mutation():
    trace_data = {
        "type": "CALL",
        "from": "0xaaa",
        "to": "0xbbb",
        "logs": [
            {
                "data": "0x1234",
            }
        ],
    }

    records = extract_execution_frames(
        trace_data,
        TX_HASH,
    )

    trace_data["logs"][0]["data"] = (
        "0xchanged"
    )

    assert (
        records[0]["frame"]["logs"][0]["data"]
        == "0x1234"
    )


@pytest.mark.parametrize(
    "frame_type",
    [
        None,
        1234,
        True,
    ],
)
def test_execution_rejects_non_string_frame_type(
    frame_type,
):
    trace_data = {
        "type": "CALL",
        "from": "0xaaa",
        "to": "0xbbb",
        "calls": [
            {
                "type": frame_type,
                "from": "0xbbb",
                "to": "0xccc",
            },
        ],
    }

    with pytest.raises(
        ValueError,
        match="Execution frame type must be a string",
    ):
        extract_execution_frames(
            trace_data,
            TX_HASH,
        )

def test_execution_preserves_unknown_string_type():
    trace_data = {
        "type": "FUTURE_EXECUTION_TYPE",
        "from": "0xaaa",
        "to": "0xbbb",
    }

    records = extract_execution_frames(
        trace_data,
        TX_HASH,
    )

    assert (
        records[0]["frame"]["type"]
        == "FUTURE_EXECUTION_TYPE"
    )
