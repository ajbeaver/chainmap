import copy
import logging
from collections.abc import Mapping

from modules.validation import (
    validate_32byte_hash,
    validate_address,
)


logger = logging.getLogger(__name__)


def create_map(chain_id):
    if (
        not isinstance(chain_id, int)
        or isinstance(chain_id, bool)
        or chain_id < 0
    ):
        raise ValueError(
            "Chain ID must be a non-negative integer"
        )

    chain_map = {
        "chain_id": chain_id,
        "nodes": {},
        "edges": {},
    }

    logger.debug(
        "Created chain map: chainId=%s",
        chain_id,
    )

    return chain_map


def ingest_relationships(
    chain_map,
    relationships,
):
    logger.info(
        "Ingesting relationship observations"
    )

    _validate_map(chain_map)

    if not isinstance(relationships, list):
        raise ValueError(
            "Relationships must be a list"
        )

    existing_observations = (
        _collect_existing_observations(
            chain_map
        )
    )

    pending = []

    for relationship in relationships:
        canonical_from, canonical_to = (
            _validate_relationship(
                relationship
            )
        )

        observation_key = (
            _observation_key(
                relationship
            )
        )

        if observation_key in existing_observations:
            existing = existing_observations[
                observation_key
            ]

            if existing != relationship:
                raise ValueError(
                    "Conflicting relationship observation "
                    "for transaction hash and frame path"
                )

            continue

        existing_observations[
            observation_key
        ] = relationship

        pending.append(
            (
                canonical_from,
                canonical_to,
                copy.deepcopy(
                    relationship
                ),
            )
        )

    for (
        canonical_from,
        canonical_to,
        relationship,
    ) in pending:
        chain_map["nodes"].setdefault(
            canonical_from,
            {},
        )

        chain_map["nodes"].setdefault(
            canonical_to,
            {},
        )

        source_edges = (
            chain_map["edges"].setdefault(
                canonical_from,
                {},
            )
        )

        edge = source_edges.setdefault(
            canonical_to,
            {
                "observations": [],
            },
        )

        edge["observations"].append(
            relationship
        )

    logger.debug(
        "Relationship ingestion completed: "
        "received=%s added=%s nodes=%s",
        len(relationships),
        len(pending),
        len(chain_map["nodes"]),
    )

    return chain_map


def _validate_map(chain_map):
    if not isinstance(chain_map, dict):
        raise ValueError(
            "Chain map must be a dictionary"
        )

    if "chain_id" not in chain_map:
        raise ValueError(
            "Chain map must include chain_id"
        )

    if (
        not isinstance(
            chain_map["chain_id"],
            int,
        )
        or isinstance(
            chain_map["chain_id"],
            bool,
        )
        or chain_map["chain_id"] < 0
    ):
        raise ValueError(
            "Chain map chain_id must be "
            "a non-negative integer"
        )

    if "nodes" not in chain_map:
        raise ValueError(
            "Chain map must include nodes"
        )

    if not isinstance(
        chain_map["nodes"],
        dict,
    ):
        raise ValueError(
            "Chain map nodes must be a dictionary"
        )

    if "edges" not in chain_map:
        raise ValueError(
            "Chain map must include edges"
        )

    if not isinstance(
        chain_map["edges"],
        dict,
    ):
        raise ValueError(
            "Chain map edges must be a dictionary"
        )


def _validate_relationship(relationship):
    if not isinstance(
        relationship,
        Mapping,
    ):
        raise ValueError(
            "Relationship must be a mapping"
        )

    required_fields = (
        "from",
        "to",
        "type",
        "transaction_hash",
        "frame_path",
        "evidence",
    )

    for field in required_fields:
        if field not in relationship:
            raise ValueError(
                f"Relationship must include {field}"
            )

    source = relationship["from"]
    target = relationship["to"]
    relationship_type = relationship["type"]
    transaction_hash = relationship[
        "transaction_hash"
    ]
    frame_path = relationship[
        "frame_path"
    ]
    evidence = relationship["evidence"]

    source = validate_address(
        source
    )

    target = validate_address(
        target
    )

    validate_32byte_hash(
        transaction_hash,
        "transaction hash",
    )

    if not isinstance(relationship_type, str):
        raise ValueError(
            "Relationship type must be a string"
        )

    if not isinstance(frame_path, list):
        raise ValueError(
            "Relationship frame_path "
            "must be a list"
        )

    if not frame_path:
        raise ValueError(
            "Relationship frame_path "
            "must not be empty"
        )

    if not all(
        isinstance(index, int)
        and not isinstance(index, bool)
        and index >= 0
        for index in frame_path
    ):
        raise ValueError(
            "Relationship frame_path must "
            "contain non-negative integers"
        )

    if not isinstance(evidence, Mapping):
        raise ValueError(
            "Relationship evidence "
            "must be a mapping"
        )

    if evidence.get("from") != source:
        raise ValueError(
            "Relationship from does not "
            "match evidence"
        )

    if evidence.get("to") != target:
        raise ValueError(
            "Relationship to does not "
            "match evidence"
        )

    if evidence.get("type") != relationship_type:
        raise ValueError(
            "Relationship type does not "
            "match evidence"
        )

    return (
        source.lower(),
        target.lower(),
    )


def _observation_key(relationship):
    return (
        relationship[
            "transaction_hash"
        ].lower(),
        tuple(
            relationship[
                "frame_path"
            ]
        ),
    )


def _collect_existing_observations(
    chain_map,
):
    observations = {}

    for source, targets in (
        chain_map["edges"].items()
    ):
        if not isinstance(targets, dict):
            raise ValueError(
                "Chain map edge targets "
                "must be a dictionary"
            )

        for target, edge in targets.items():
            if not isinstance(edge, Mapping):
                raise ValueError(
                    "Chain map edge must "
                    "be a mapping"
                )

            if "observations" not in edge:
                raise ValueError(
                    "Chain map edge must "
                    "include observations"
                )

            edge_observations = edge[
                "observations"
            ]

            if not isinstance(
                edge_observations,
                list,
            ):
                raise ValueError(
                    "Chain map edge observations "
                    "must be a list"
                )

            for observation in (
                edge_observations
            ):
                canonical_from, canonical_to = (
                    _validate_relationship(
                        observation
                    )
                )

                if canonical_from != source:
                    raise ValueError(
                        "Relationship source does "
                        "not match map edge"
                    )

                if canonical_to != target:
                    raise ValueError(
                        "Relationship target does "
                        "not match map edge"
                    )

                key = _observation_key(
                    observation
                )

                if key in observations:
                    if (
                        observations[key]
                        != observation
                    ):
                        raise ValueError(
                            "Conflicting duplicate "
                            "observation in chain map"
                        )

                    raise ValueError(
                        "Duplicate observation "
                        "in chain map"
                    )

                observations[key] = (
                    observation
                )

    return observations
