import pytest
from web3.exceptions import TransactionNotFound

from conftest import UNKNOWN_HASH

from modules.orchestration import (
    collect_transaction_relationships,
    create_chainmap_for_rpc,
    ingest_relationship_batch,
    ingest_transaction,
)


ADDRESS_A = (
    "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266"
)

ADDRESS_B = (
    "0x70997970c51812dc3a010c7d01b50e0d17dc79c8"
)

ADDRESS_C = (
    "0x3c44cdddb6a900fa2b585dd299e03d12fa4293bc"
)

TX_HASH_1 = "0x" + "11" * 32
TX_HASH_2 = "0x" + "22" * 32


def build_relationship(
    source=ADDRESS_A,
    target=ADDRESS_B,
    transaction_hash=TX_HASH_1,
):
    return {
        "from": source,
        "to": target,
        "type": "CALL",
        "transaction_hash": transaction_hash,
        "frame_path": [0],
        "evidence": {
            "type": "CALL",
            "from": source,
            "to": target,
        },
    }


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


def test_relationship_collection_is_independent_of_map(
    w3,
    chain_state,
):
    relationships = (
        collect_transaction_relationships(
            w3,
            chain_state[
                "nested_call_tx_hash"
            ],
        )
    )

    assert isinstance(
        relationships,
        list,
    )

    assert relationships


def test_relationship_batch_writer_mutates_map():
    chain_map = {
        "chain_id": 1,
        "nodes": {},
        "edges": {},
    }

    relationship = build_relationship()

    result = ingest_relationship_batch(
        chain_map,
        [relationship],
    )

    assert result is chain_map

    assert (
        ADDRESS_B
        in chain_map[
            "edges"
        ][ADDRESS_A]
    )


def test_sequential_relationship_batches_preserve_all_observations():
    chain_map = {
        "chain_id": 1,
        "nodes": {},
        "edges": {},
    }

    first = build_relationship(
        source=ADDRESS_A,
        target=ADDRESS_B,
        transaction_hash=TX_HASH_1,
    )

    second = build_relationship(
        source=ADDRESS_B,
        target=ADDRESS_C,
        transaction_hash=TX_HASH_2,
    )

    ingest_relationship_batch(
        chain_map,
        [first],
    )

    ingest_relationship_batch(
        chain_map,
        [second],
    )

    assert (
        ADDRESS_B
        in chain_map[
            "edges"
        ][ADDRESS_A]
    )

    assert (
        ADDRESS_C
        in chain_map[
            "edges"
        ][ADDRESS_B]
    )


def test_sequential_duplicate_batch_remains_idempotent():
    chain_map = {
        "chain_id": 1,
        "nodes": {},
        "edges": {},
    }

    relationship = build_relationship()

    ingest_relationship_batch(
        chain_map,
        [relationship],
    )

    ingest_relationship_batch(
        chain_map,
        [relationship],
    )

    observations = chain_map[
        "edges"
    ][ADDRESS_A][ADDRESS_B][
        "observations"
    ]

    assert len(observations) == 1


def test_sequential_conflicting_batch_raises():
    chain_map = {
        "chain_id": 1,
        "nodes": {},
        "edges": {},
    }

    first = build_relationship()

    conflicting = build_relationship()
    conflicting["type"] = "STATICCALL"
    conflicting[
        "evidence"
    ][
        "type"
    ] = "STATICCALL"

    ingest_relationship_batch(
        chain_map,
        [first],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Conflicting relationship observation "
            "for transaction hash and frame path"
        ),
    ):
        ingest_relationship_batch(
            chain_map,
            [conflicting],
        )


def test_ingest_transaction_uses_writer_path(
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

    relationships = []
    seen = {}

    def fake_collect(
        received_w3,
        tx_hash,
    ):
        seen["producer_w3"] = (
            received_w3
        )

        return relationships

    def fake_ingest(
        received_map,
        received_relationships,
    ):
        seen["map"] = received_map
        seen["relationships"] = (
            received_relationships
        )

        return received_map

    monkeypatch.setattr(
        (
            "modules.orchestration."
            "collect_transaction_relationships"
        ),
        fake_collect,
    )

    monkeypatch.setattr(
        (
            "modules.orchestration."
            "ingest_relationship_batch"
        ),
        fake_ingest,
    )

    ingest_transaction(
        w3,
        chain_map,
        TX_HASH_1,
    )

    assert (
        seen["producer_w3"]
        is w3
    )

    assert (
        seen["map"]
        is chain_map
    )

    assert (
        seen["relationships"]
        is relationships
    )


def test_collection_uses_same_rpc_object(
    monkeypatch,
):
    class FakeEth:
        chain_id = 1

    class FakeWeb3:
        eth = FakeEth()

    w3 = FakeWeb3()

    seen = {}

    def fake_generate_transaction_data(
        received_w3,
        tx_hash,
    ):
        seen["transaction_w3"] = (
            received_w3
        )

        return {
            "hash": tx_hash,
        }

    def fake_generate_trace_data(
        received_w3,
        tx_hash,
        options,
    ):
        seen["trace_w3"] = (
            received_w3
        )

        return {
            "type": "CALL",
        }

    monkeypatch.setattr(
        (
            "modules.orchestration."
            "generate_transaction_data"
        ),
        fake_generate_transaction_data,
    )

    monkeypatch.setattr(
        (
            "modules.orchestration."
            "generate_trace_data"
        ),
        fake_generate_trace_data,
    )

    relationships = (
        collect_transaction_relationships(
            w3,
            TX_HASH_1,
        )
    )

    assert relationships == []

    assert (
        seen["transaction_w3"]
        is w3
    )

    assert (
        seen["trace_w3"]
        is w3
    )


def test_unknown_transaction_stops_before_trace(
    w3,
    monkeypatch,
):
    trace_called = False

    def fake_generate_trace_data(
        w3,
        tx_hash,
        options,
    ):
        nonlocal trace_called

        trace_called = True

        raise AssertionError(
            "Trace must not be requested "
            "for an unknown transaction"
        )

    monkeypatch.setattr(
        (
            "modules.orchestration."
            "generate_trace_data"
        ),
        fake_generate_trace_data,
    )

    with pytest.raises(
        TransactionNotFound
    ):
        collect_transaction_relationships(
            w3,
            UNKNOWN_HASH,
        )

    assert trace_called is False


def test_unknown_transaction_does_not_mutate_map(
    w3,
    monkeypatch,
):
    chain_map = create_chainmap_for_rpc(
        w3
    )

    writer_called = False

    def fake_ingest(
        chain_map,
        relationships,
    ):
        nonlocal writer_called

        writer_called = True

        raise AssertionError(
            "Writer must not run for "
            "an unknown transaction"
        )

    monkeypatch.setattr(
        (
            "modules.orchestration."
            "ingest_relationship_batch"
        ),
        fake_ingest,
    )

    with pytest.raises(
        TransactionNotFound
    ):
        ingest_transaction(
            w3,
            chain_map,
            UNKNOWN_HASH,
        )

    assert writer_called is False

    assert chain_map == {
        "chain_id": w3.eth.chain_id,
        "nodes": {},
        "edges": {},
    }
