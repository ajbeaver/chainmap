import copy

import pytest

from modules.execution import extract_execution_frames
from modules.map import create_map, ingest_relationships
from modules.relationships import extract_relationships
from modules.trace import generate_trace_data


CHAIN_ID = 31337

TX_HASH_1 = "0x" + "11" * 32
TX_HASH_2 = "0x" + "22" * 32

ADDRESS_A = (
    "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266"
)

ADDRESS_B = (
    "0x70997970c51812dc3a010c7d01b50e0d17dc79c8"
)

ADDRESS_C = (
    "0x3c44cdddb6a900fa2b585dd299e03d12fa4293bc"
)

CHECKSUM_A = (
    "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
)

CHECKSUM_B = (
    "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
)


def build_relationship(
    source=ADDRESS_A,
    target=ADDRESS_B,
    relationship_type="CALL",
    transaction_hash=TX_HASH_1,
    frame_path=None,
    **evidence_fields,
):
    if frame_path is None:
        frame_path = [0]

    evidence = {
        "type": relationship_type,
        "from": source,
        "to": target,
        "value": "0x0",
    }

    evidence.update(
        evidence_fields
    )

    return {
        "from": source,
        "to": target,
        "type": relationship_type,
        "transaction_hash": transaction_hash,
        "frame_path": frame_path,
        "evidence": evidence,
    }


def test_create_map_returns_empty_map():
    chain_map = create_map(
        CHAIN_ID
    )

    assert chain_map == {
        "chain_id": CHAIN_ID,
        "nodes": {},
        "edges": {},
    }


@pytest.mark.parametrize(
    "chain_id",
    [
        -1,
        True,
        "31337",
        31337.0,
        None,
    ],
)
def test_create_map_rejects_invalid_chain_id(
    chain_id,
):
    with pytest.raises(
        ValueError,
        match=(
            "Chain ID must be "
            "a non-negative integer"
        ),
    ):
        create_map(
            chain_id
        )


def test_ingest_relationship_creates_nodes_and_edge():
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship()

    result = ingest_relationships(
        chain_map,
        [relationship],
    )

    assert result is chain_map

    assert chain_map["nodes"] == {
        ADDRESS_A: {},
        ADDRESS_B: {},
    }

    assert set(
        chain_map["edges"]
    ) == {
        ADDRESS_A,
    }

    assert set(
        chain_map["edges"][ADDRESS_A]
    ) == {
        ADDRESS_B,
    }

    edge = chain_map[
        "edges"
    ][ADDRESS_A][ADDRESS_B]

    assert set(edge) == {
        "observations",
    }

    assert edge["observations"] == [
        relationship
    ]


def test_ingest_canonicalizes_only_map_keys():
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship(
        source=CHECKSUM_A,
        target=CHECKSUM_B,
    )

    ingest_relationships(
        chain_map,
        [relationship],
    )

    assert ADDRESS_A in chain_map["nodes"]
    assert ADDRESS_B in chain_map["nodes"]

    stored = chain_map[
        "edges"
    ][ADDRESS_A][ADDRESS_B][
        "observations"
    ][0]

    assert stored["from"] == CHECKSUM_A
    assert stored["to"] == CHECKSUM_B

    assert (
        stored["evidence"]["from"]
        == CHECKSUM_A
    )

    assert (
        stored["evidence"]["to"]
        == CHECKSUM_B
    )


def test_same_edge_preserves_multiple_observations():
    chain_map = create_map(
        CHAIN_ID
    )

    first = build_relationship(
        relationship_type="CALL",
        transaction_hash=TX_HASH_1,
        frame_path=[0],
    )

    second = build_relationship(
        relationship_type="STATICCALL",
        transaction_hash=TX_HASH_2,
        frame_path=[0],
    )

    ingest_relationships(
        chain_map,
        [
            first,
            second,
        ],
    )

    observations = chain_map[
        "edges"
    ][ADDRESS_A][ADDRESS_B][
        "observations"
    ]

    assert observations == [
        first,
        second,
    ]


def test_map_preserves_directionality():
    chain_map = create_map(
        CHAIN_ID
    )

    forward = build_relationship(
        source=ADDRESS_A,
        target=ADDRESS_B,
        transaction_hash=TX_HASH_1,
    )

    reverse = build_relationship(
        source=ADDRESS_B,
        target=ADDRESS_A,
        transaction_hash=TX_HASH_2,
    )

    ingest_relationships(
        chain_map,
        [
            forward,
            reverse,
        ],
    )

    assert (
        ADDRESS_B
        in chain_map["edges"][ADDRESS_A]
    )

    assert (
        ADDRESS_A
        in chain_map["edges"][ADDRESS_B]
    )


def test_exact_reingestion_is_idempotent():
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship()

    ingest_relationships(
        chain_map,
        [relationship],
    )

    original = copy.deepcopy(
        chain_map
    )

    ingest_relationships(
        chain_map,
        [relationship],
    )

    assert chain_map == original


def test_duplicate_within_same_batch_is_idempotent():
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship()

    ingest_relationships(
        chain_map,
        [
            relationship,
            copy.deepcopy(
                relationship
            ),
        ],
    )

    observations = chain_map[
        "edges"
    ][ADDRESS_A][ADDRESS_B][
        "observations"
    ]

    assert len(observations) == 1


def test_conflicting_observation_raises():
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship()

    ingest_relationships(
        chain_map,
        [relationship],
    )

    original = copy.deepcopy(
        chain_map
    )

    conflicting = build_relationship(
        relationship_type="STATICCALL",
        transaction_hash=TX_HASH_1,
        frame_path=[0],
    )

    with pytest.raises(
        ValueError,
        match=(
            "Conflicting relationship observation "
            "for transaction hash and frame path"
        ),
    ):
        ingest_relationships(
            chain_map,
            [conflicting],
        )

    assert chain_map == original


def test_conflict_within_batch_is_atomic():
    chain_map = create_map(
        CHAIN_ID
    )

    first = build_relationship(
        relationship_type="CALL",
        transaction_hash=TX_HASH_1,
        frame_path=[0],
    )

    conflicting = build_relationship(
        relationship_type="STATICCALL",
        transaction_hash=TX_HASH_1,
        frame_path=[0],
    )

    original = copy.deepcopy(
        chain_map
    )

    with pytest.raises(
        ValueError,
        match=(
            "Conflicting relationship observation "
            "for transaction hash and frame path"
        ),
    ):
        ingest_relationships(
            chain_map,
            [
                first,
                conflicting,
            ],
        )

    assert chain_map == original


def test_invalid_batch_is_atomic():
    chain_map = create_map(
        CHAIN_ID
    )

    existing = build_relationship(
        transaction_hash=TX_HASH_1,
    )

    ingest_relationships(
        chain_map,
        [existing],
    )

    original = copy.deepcopy(
        chain_map
    )

    valid = build_relationship(
        source=ADDRESS_B,
        target=ADDRESS_C,
        transaction_hash=TX_HASH_2,
        frame_path=[0],
    )

    invalid = build_relationship(
        transaction_hash="0x1234",
        frame_path=[0, 1],
    )

    with pytest.raises(ValueError):
        ingest_relationships(
            chain_map,
            [
                valid,
                invalid,
            ],
        )

    assert chain_map == original


def test_ingest_does_not_alias_input():
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship(
        customField="preserve-me",
    )

    ingest_relationships(
        chain_map,
        [relationship],
    )

    relationship[
        "frame_path"
    ].append(99)

    relationship[
        "evidence"
    ][
        "customField"
    ] = "changed"

    stored = chain_map[
        "edges"
    ][ADDRESS_A][ADDRESS_B][
        "observations"
    ][0]

    assert stored["frame_path"] == [0]

    assert (
        stored["evidence"][
            "customField"
        ]
        == "preserve-me"
    )


def test_map_observation_does_not_alias_input():
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship(
        customField="preserve-me",
    )

    ingest_relationships(
        chain_map,
        [relationship],
    )

    stored = chain_map[
        "edges"
    ][ADDRESS_A][ADDRESS_B][
        "observations"
    ][0]

    stored[
        "frame_path"
    ].append(99)

    stored[
        "evidence"
    ][
        "customField"
    ] = "changed"

    assert (
        relationship["frame_path"]
        == [0]
    )

    assert (
        relationship["evidence"][
            "customField"
        ]
        == "preserve-me"
    )


def test_empty_ingestion_leaves_map_unchanged():
    chain_map = create_map(
        CHAIN_ID
    )

    original = copy.deepcopy(
        chain_map
    )

    result = ingest_relationships(
        chain_map,
        [],
    )

    assert result is chain_map
    assert chain_map == original


def test_map_does_not_add_derived_fields():
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship()

    ingest_relationships(
        chain_map,
        [relationship],
    )

    assert chain_map[
        "nodes"
    ][ADDRESS_A] == {}

    edge = chain_map[
        "edges"
    ][ADDRESS_A][ADDRESS_B]

    assert set(edge) == {
        "observations",
    }

    assert "count" not in edge
    assert "types" not in edge
    assert "first_seen" not in edge
    assert "last_seen" not in edge


def test_ingest_rejects_non_list_relationships():
    chain_map = create_map(
        CHAIN_ID
    )

    with pytest.raises(
        ValueError,
        match="Relationships must be a list",
    ):
        ingest_relationships(
            chain_map,
            {},
        )


def test_ingest_rejects_non_mapping_relationship():
    chain_map = create_map(
        CHAIN_ID
    )

    with pytest.raises(
        ValueError,
        match="Relationship must be a mapping",
    ):
        ingest_relationships(
            chain_map,
            [
                "not-a-relationship",
            ],
        )


@pytest.mark.parametrize(
    ("field", "message"),
    [
        (
            "from",
            "Relationship must include from",
        ),
        (
            "to",
            "Relationship must include to",
        ),
        (
            "type",
            "Relationship must include type",
        ),
        (
            "transaction_hash",
            (
                "Relationship must include "
                "transaction_hash"
            ),
        ),
        (
            "frame_path",
            (
                "Relationship must include "
                "frame_path"
            ),
        ),
        (
            "evidence",
            (
                "Relationship must include "
                "evidence"
            ),
        ),
    ],
)
def test_ingest_rejects_missing_relationship_fields(
    field,
    message,
):
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship()

    del relationship[field]

    with pytest.raises(
        ValueError,
        match=message,
    ):
        ingest_relationships(
            chain_map,
            [relationship],
        )


@pytest.mark.parametrize(
    "address_field",
    [
        "from",
        "to",
    ],
)
def test_ingest_rejects_invalid_addresses(
    address_field,
):
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship()

    relationship[
        address_field
    ] = "0x1234"

    relationship[
        "evidence"
    ][
        address_field
    ] = "0x1234"

    with pytest.raises(ValueError):
        ingest_relationships(
            chain_map,
            [relationship],
        )


def test_ingest_rejects_invalid_transaction_hash():
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship(
        transaction_hash="0x1234",
    )

    with pytest.raises(
        ValueError,
        match=(
            "transaction hash must be "
            "exactly 32 bytes"
        ),
    ):
        ingest_relationships(
            chain_map,
            [relationship],
        )


@pytest.mark.parametrize(
    "relationship_type",
    [
        None,
        1234,
        True,
    ],
)
def test_ingest_rejects_non_string_type(
    relationship_type,
):
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship(
        relationship_type=relationship_type,
    )

    with pytest.raises(
        ValueError,
        match="Relationship type must be a string",
    ):
        ingest_relationships(
            chain_map,
            [relationship],
        )


def test_ingest_preserves_unknown_type():
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship(
        relationship_type=(
            "FUTURE_EXECUTION_TYPE"
        ),
    )

    ingest_relationships(
        chain_map,
        [relationship],
    )

    stored = chain_map[
        "edges"
    ][ADDRESS_A][ADDRESS_B][
        "observations"
    ][0]

    assert (
        stored["type"]
        == "FUTURE_EXECUTION_TYPE"
    )


@pytest.mark.parametrize(
    "frame_path",
    [
        [],
        "0.1",
        [0, -1],
        [0, "1"],
        [0, 1.5],
        [0, None],
        [0, True],
    ],
)
def test_ingest_rejects_invalid_frame_path(
    frame_path,
):
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship(
        frame_path=frame_path,
    )

    with pytest.raises(ValueError):
        ingest_relationships(
            chain_map,
            [relationship],
        )


def test_ingest_rejects_non_mapping_evidence():
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship()

    relationship[
        "evidence"
    ] = []

    with pytest.raises(
        ValueError,
        match=(
            "Relationship evidence "
            "must be a mapping"
        ),
    ):
        ingest_relationships(
            chain_map,
            [relationship],
        )


@pytest.mark.parametrize(
    ("field", "message"),
    [
        (
            "from",
            (
                "Relationship from does not "
                "match evidence"
            ),
        ),
        (
            "to",
            (
                "Relationship to does not "
                "match evidence"
            ),
        ),
        (
            "type",
            (
                "Relationship type does not "
                "match evidence"
            ),
        ),
    ],
)
def test_ingest_rejects_promoted_evidence_mismatch(
    field,
    message,
):
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship()

    if field == "from":
        relationship[
            "evidence"
        ][field] = ADDRESS_C

    elif field == "to":
        relationship[
            "evidence"
        ][field] = ADDRESS_C

    else:
        relationship[
            "evidence"
        ][field] = "STATICCALL"

    with pytest.raises(
        ValueError,
        match=message,
    ):
        ingest_relationships(
            chain_map,
            [relationship],
        )


def test_ingest_rejects_non_dictionary_map():
    with pytest.raises(
        ValueError,
        match=(
            "Chain map must be a dictionary"
        ),
    ):
        ingest_relationships(
            [],
            [],
        )


@pytest.mark.parametrize(
    ("chain_map", "message"),
    [
        (
            {
                "nodes": {},
                "edges": {},
            },
            "Chain map must include chain_id",
        ),
        (
            {
                "chain_id": True,
                "nodes": {},
                "edges": {},
            },
            (
                "Chain map chain_id must be "
                "a non-negative integer"
            ),
        ),
        (
            {
                "chain_id": CHAIN_ID,
                "edges": {},
            },
            "Chain map must include nodes",
        ),
        (
            {
                "chain_id": CHAIN_ID,
                "nodes": [],
                "edges": {},
            },
            (
                "Chain map nodes must be "
                "a dictionary"
            ),
        ),
        (
            {
                "chain_id": CHAIN_ID,
                "nodes": {},
            },
            "Chain map must include edges",
        ),
        (
            {
                "chain_id": CHAIN_ID,
                "nodes": {},
                "edges": [],
            },
            (
                "Chain map edges must be "
                "a dictionary"
            ),
        ),
    ],
)
def test_ingest_rejects_invalid_map_structure(
    chain_map,
    message,
):
    with pytest.raises(
        ValueError,
        match=message,
    ):
        ingest_relationships(
            chain_map,
            [],
        )


def test_ingest_rejects_invalid_edge_targets():
    chain_map = create_map(
        CHAIN_ID
    )

    chain_map["edges"][
        ADDRESS_A
    ] = []

    with pytest.raises(
        ValueError,
        match=(
            "Chain map edge targets "
            "must be a dictionary"
        ),
    ):
        ingest_relationships(
            chain_map,
            [],
        )


def test_ingest_rejects_non_mapping_edge():
    chain_map = create_map(
        CHAIN_ID
    )

    chain_map["edges"] = {
        ADDRESS_A: {
            ADDRESS_B: [],
        },
    }

    with pytest.raises(
        ValueError,
        match="Chain map edge must be a mapping",
    ):
        ingest_relationships(
            chain_map,
            [],
        )


def test_ingest_rejects_edge_without_observations():
    chain_map = create_map(
        CHAIN_ID
    )

    chain_map["edges"] = {
        ADDRESS_A: {
            ADDRESS_B: {},
        },
    }

    with pytest.raises(
        ValueError,
        match=(
            "Chain map edge must include "
            "observations"
        ),
    ):
        ingest_relationships(
            chain_map,
            [],
        )


def test_ingest_rejects_non_list_edge_observations():
    chain_map = create_map(
        CHAIN_ID
    )

    chain_map["edges"] = {
        ADDRESS_A: {
            ADDRESS_B: {
                "observations": {},
            },
        },
    }

    with pytest.raises(
        ValueError,
        match=(
            "Chain map edge observations "
            "must be a list"
        ),
    ):
        ingest_relationships(
            chain_map,
            [],
        )


def test_ingest_rejects_wrong_source_edge():
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship(
        source=ADDRESS_A,
        target=ADDRESS_B,
    )

    chain_map["edges"] = {
        ADDRESS_C: {
            ADDRESS_B: {
                "observations": [
                    relationship,
                ],
            },
        },
    }

    with pytest.raises(
        ValueError,
        match=(
            "Relationship source does not "
            "match map edge"
        ),
    ):
        ingest_relationships(
            chain_map,
            [],
        )


def test_ingest_rejects_wrong_target_edge():
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship(
        source=ADDRESS_A,
        target=ADDRESS_B,
    )

    chain_map["edges"] = {
        ADDRESS_A: {
            ADDRESS_C: {
                "observations": [
                    relationship,
                ],
            },
        },
    }

    with pytest.raises(
        ValueError,
        match=(
            "Relationship target does not "
            "match map edge"
        ),
    ):
        ingest_relationships(
            chain_map,
            [],
        )


def test_ingest_rejects_duplicate_existing_observation():
    chain_map = create_map(
        CHAIN_ID
    )

    relationship = build_relationship()

    chain_map["nodes"] = {
        ADDRESS_A: {},
        ADDRESS_B: {},
    }

    chain_map["edges"] = {
        ADDRESS_A: {
            ADDRESS_B: {
                "observations": [
                    copy.deepcopy(
                        relationship
                    ),
                    copy.deepcopy(
                        relationship
                    ),
                ],
            },
        },
    }

    with pytest.raises(
        ValueError,
        match=(
            "Duplicate observation "
            "in chain map"
        ),
    ):
        ingest_relationships(
            chain_map,
            [],
        )


def test_ingest_rejects_conflicting_existing_observation():
    chain_map = create_map(
        CHAIN_ID
    )

    first = build_relationship(
        relationship_type="CALL",
        transaction_hash=TX_HASH_1,
        frame_path=[0],
    )

    conflicting = build_relationship(
        relationship_type="STATICCALL",
        transaction_hash=TX_HASH_1,
        frame_path=[0],
    )

    chain_map["nodes"] = {
        ADDRESS_A: {},
        ADDRESS_B: {},
    }

    chain_map["edges"] = {
        ADDRESS_A: {
            ADDRESS_B: {
                "observations": [
                    first,
                    conflicting,
                ],
            },
        },
    }

    with pytest.raises(
        ValueError,
        match=(
            "Conflicting duplicate observation "
            "in chain map"
        ),
    ):
        ingest_relationships(
            chain_map,
            [],
        )


def test_map_composes_with_full_pipeline(
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

    chain_map = create_map(
        w3.eth.chain_id
    )

    ingest_relationships(
        chain_map,
        relationships,
    )

    account = relationships[
        0
    ]["from"].lower()

    caller = chain_state[
        "caller_contract"
    ].lower()

    middle = chain_state[
        "middle_contract"
    ].lower()

    leaf = chain_state[
        "leaf_contract"
    ].lower()

    assert set(
        chain_map["nodes"]
    ) == {
        account,
        caller,
        middle,
        leaf,
    }

    assert (
        caller
        in chain_map["edges"][account]
    )

    assert (
        middle
        in chain_map["edges"][caller]
    )

    assert (
        leaf
        in chain_map["edges"][middle]
    )

    observations = []

    for targets in (
        chain_map["edges"].values()
    ):
        for edge in targets.values():
            observations.extend(
                edge["observations"]
            )

    assert len(observations) == 3

    assert {
        tuple(
            observation["frame_path"]
        )
        for observation in observations
    } == {
        (0,),
        (0, 0),
        (0, 0, 0),
    }

    for observation in observations:
        assert (
            observation[
                "transaction_hash"
            ]
            == tx_hash
        )
