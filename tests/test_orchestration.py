import pytest

from modules.orchestration import (
    create_chainmap_for_rpc,
    ingest_transaction,
)


def test_chainmap_uses_rpc_chain_id(
    w3,
):
    chain_map = create_chainmap_for_rpc(
        w3
    )

    assert (
        chain_map["chain_id"]
        == w3.eth.chain_id
    )


def test_transaction_pipeline_uses_same_rpc(
    w3,
    chain_state,
):
    chain_map = create_chainmap_for_rpc(
        w3
    )

    result = ingest_transaction(
        w3,
        chain_map,
        chain_state[
            "nested_call_tx_hash"
        ],
    )

    assert result is chain_map
    assert chain_map["edges"]


def test_transaction_rejects_different_rpc_chain(
    w3,
    chain_state,
):
    chain_map = create_chainmap_for_rpc(
        w3
    )

    chain_map["chain_id"] = (
        w3.eth.chain_id + 1
    )

    with pytest.raises(
        ValueError,
        match=(
            "Chain map chain_id does not "
            "match RPC chain_id"
        ),
    ):
        ingest_transaction(
            w3,
            chain_map,
            chain_state[
                "nested_call_tx_hash"
            ],
        )

def test_ingest_transaction_uses_same_rpc_object(
    monkeypatch,
):
    class FakeEth:
        chain_id = 1

    class FakeWeb3:
        eth = FakeEth()

    w3 = FakeWeb3()

    chain_map = {
        "chain_id": 1,
        "nodes": {},
        "edges": {},
    }

    seen = {}

    def fake_generate_trace_data(
        received_w3,
        tx_hash,
        options,
    ):
        seen["w3"] = received_w3

        return {
            "type": "CALL",
        }

    monkeypatch.setattr(
        "modules.orchestration.generate_trace_data",
        fake_generate_trace_data,
    )

    ingest_transaction(
        w3,
        chain_map,
        "0x" + "11" * 32,
    )

    assert seen["w3"] is w3
