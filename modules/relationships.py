import copy
import logging
from collections.abc import Mapping


logger = logging.getLogger(__name__)


def extract_relationships(execution_records):
    logger.info(
        "Extracting execution relationships"
    )

    if not isinstance(execution_records, list):
        raise ValueError(
            "Execution records must be a list"
        )

    relationships = []

    for record in execution_records:
        if not isinstance(record, Mapping):
            raise ValueError(
                "Execution record must be a mapping"
            )

        if "transaction_hash" not in record:
            raise ValueError(
                "Execution record must include transaction_hash"
            )

        if "frame_path" not in record:
            raise ValueError(
                "Execution record must include frame_path"
            )

        if "frame" not in record:
            raise ValueError(
                "Execution record must include frame"
            )

        transaction_hash = record[
            "transaction_hash"
        ]

        frame_path = record[
            "frame_path"
        ]

        frame = record[
            "frame"
        ]

        if not isinstance(transaction_hash, str):
            raise ValueError(
                "Execution record transaction_hash "
                "must be a string"
            )

        if not isinstance(frame_path, list):
            raise ValueError(
                "Execution record frame_path "
                "must be a list"
            )

        if not frame_path:
            raise ValueError(
                "Execution record frame_path "
                "must not be empty"
            )

        if not all(
            isinstance(index, int)
            and not isinstance(index, bool)
            and index >= 0
            for index in frame_path
        ):
            raise ValueError(
                "Execution record frame_path "
                "must contain non-negative integers"
            )

        if not isinstance(frame, Mapping):
            raise ValueError(
                "Execution record frame "
                "must be a mapping"
            )

        if "type" not in frame:
            raise ValueError(
                "Execution frame must include type"
            )

        if not isinstance(frame["type"], str):
            raise ValueError(
                "Execution frame type must be a string"
            )

        if (
            "from" not in frame
            or "to" not in frame
        ):
            continue

        if (
            frame["from"] is None
            or frame["to"] is None
        ):
            continue

        relationships.append({
            "from": frame["from"],
            "to": frame["to"],
            "type": frame["type"],
            "transaction_hash": transaction_hash,
            "frame_path": copy.deepcopy(
                frame_path
            ),
            "evidence": copy.deepcopy(
                frame
            ),
        })

    logger.debug(
        "Relationship extraction completed: "
        "executionRecords=%s relationships=%s",
        len(execution_records),
        len(relationships),
    )

    return relationships
