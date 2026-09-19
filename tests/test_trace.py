import pytest
from web3.exceptions import Web3RPCError

from modules.normalize import normalize_rpc_data
from modules.trace import generate_trace_data

from conftest import UNKNOWN_HASH


def test_default_trace_preserves_complete_rpc_response(
    w3,
    chain_state,
):
    tx_hash = chain_state["legacy_tx_hash"]

    response = w3.provider.make_request(
        "debug_traceTransaction",
        [tx_hash],
    )

    assert "error" not in response

    expected = normalize_rpc_data(
        response["result"]
    )

    actual = generate_trace_data(
        w3,
        tx_hash,
    )

    assert actual == expected


def test_call_tracer_preserves_complete_rpc_response(
    w3,
    chain_state,
):
    tx_hash = chain_state["eip1559_tx_hash"]

    options = {
        "tracer": "callTracer",
    }

    response = w3.provider.make_request(
        "debug_traceTransaction",
        [
            tx_hash,
            options,
        ],
    )

    assert "error" not in response

    expected = normalize_rpc_data(
        response["result"]
    )

    actual = generate_trace_data(
        w3,
        tx_hash,
        options,
    )

    assert actual == expected


def test_call_tracer_preserves_nested_calls(
    w3,
    chain_state,
):
    options = {
        "tracer": "callTracer",
    }

    tx_hash = chain_state[
        "nested_call_tx_hash"
    ]

    response = w3.provider.make_request(
        "debug_traceTransaction",
        [
            tx_hash,
            options,
        ],
    )

    assert "error" not in response

    expected = normalize_rpc_data(
        response["result"]
    )

    actual = generate_trace_data(
        w3,
        tx_hash,
        options,
    )

    assert actual == expected

    assert (
        actual["to"].lower()
        == chain_state["caller_contract"].lower()
    )

    first_call = actual["calls"][0]

    assert (
        first_call["from"].lower()
        == chain_state["caller_contract"].lower()
    )

    assert (
        first_call["to"].lower()
        == chain_state["middle_contract"].lower()
    )

    second_call = first_call["calls"][0]

    assert (
        second_call["from"].lower()
        == chain_state["middle_contract"].lower()
    )

    assert (
        second_call["to"].lower()
        == chain_state["leaf_contract"].lower()
    )


def test_trace_rpc_error_raises(
    w3,
    chain_state,
    monkeypatch,
):
    def fake_make_request(method, params):
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32601,
                "message": "method not found",
            },
        }

    monkeypatch.setattr(
        w3.provider,
        "make_request",
        fake_make_request,
    )

    with pytest.raises(Web3RPCError):
        generate_trace_data(
            w3,
            chain_state["legacy_tx_hash"],
        )


def test_trace_missing_result_raises(
    w3,
    chain_state,
    monkeypatch,
):
    def fake_make_request(method, params):
        return {
            "jsonrpc": "2.0",
            "id": 1,
        }

    monkeypatch.setattr(
        w3.provider,
        "make_request",
        fake_make_request,
    )

    with pytest.raises(Web3RPCError):
        generate_trace_data(
            w3,
            chain_state["legacy_tx_hash"],
        )

def test_call_tracer_preserves_execution_fields(
    w3,
    chain_state,
):
    data = generate_trace_data(
        w3,
        chain_state["legacy_tx_hash"],
        {
            "tracer": "callTracer",
        },
    )

    assert "type" in data
    assert "from" in data
    assert "to" in data
    assert "gas" in data
    assert "gasUsed" in data
    assert "input" in data
    assert "value" in data


def test_call_tracer_preserves_logs(
    w3,
    chain_state,
):
    tx_hash = chain_state["log_tx_hash"]

    options = {
        "tracer": "callTracer",
        "tracerConfig": {
            "withLog": True,
        },
    }

    response = w3.provider.make_request(
        "debug_traceTransaction",
        [
            tx_hash,
            options,
        ],
    )

    assert "error" not in response

    expected = normalize_rpc_data(
        response["result"]
    )

    actual = generate_trace_data(
        w3,
        tx_hash,
        options,
    )

    assert actual == expected
    assert "logs" in actual
    assert len(actual["logs"]) == 1


def test_trace_options_are_not_modified(
    w3,
    chain_state,
):
    options = {
        "tracer": "callTracer",
        "tracerConfig": {
            "withLog": True,
        },
    }

    expected_options = {
        "tracer": "callTracer",
        "tracerConfig": {
            "withLog": True,
        },
    }

    generate_trace_data(
        w3,
        chain_state["log_tx_hash"],
        options,
    )

    assert options == expected_options


def test_trace_invalid_hash_raises(w3):
    with pytest.raises(
        ValueError,
        match="transaction hash must be exactly 32 bytes",
    ):
        generate_trace_data(
            w3,
            "0x1234",
        )


def test_trace_unknown_transaction_preserves_rpc_response(
    w3,
):
    options = {
        "tracer": "callTracer",
    }

    response = w3.provider.make_request(
        "debug_traceTransaction",
        [
            UNKNOWN_HASH,
            options,
        ],
    )

    assert "error" not in response

    expected = normalize_rpc_data(
        response["result"]
    )

    actual = generate_trace_data(
        w3,
        UNKNOWN_HASH,
        options,
    )

    assert actual == expected
