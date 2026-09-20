import copy
import logging
from collections.abc import Mapping

from modules.validation import validate_32byte_hash


logger = logging.getLogger(__name__)


def extract_execution_frames(
    trace_data,
    tx_hash,
):
    logger.info(
        "Extracting execution frames"
    )

    try:
        tx_hash = validate_32byte_hash(
            tx_hash,
            "transaction hash",
        )

    except ValueError as exc:
        logger.error(
            "Invalid transaction hash: %s",
            exc,
        )
        logger.debug(
            "Transaction hash validation exception: %s",
            type(exc).__name__,
        )
        raise

    if not isinstance(trace_data, Mapping):
        raise ValueError(
            "Trace data must be a callTracer mapping"
        )

    if "type" not in trace_data:
        raise ValueError(
            "Trace data does not appear to be a callTracer result"
        )

    records = []

    stack = [
        (
            trace_data,
            [0],
        )
    ]

    while stack:
        frame, frame_path = stack.pop()

        if not isinstance(frame, Mapping):
            raise ValueError(
                "Execution frame must be a mapping"
            )

        children = frame.get(
            "calls",
            [],
        )

        if not isinstance(children, list):
            raise ValueError(
                "Execution frame calls must be a list"
            )

        local_frame = copy.deepcopy({
            key: value
            for key, value in frame.items()
            if key != "calls"
        })

        records.append({
            "transaction_hash": tx_hash,
            "frame_path": frame_path,
            "frame": local_frame,
        })

        for index in range(
            len(children) - 1,
            -1,
            -1,
        ):
            stack.append(
                (
                    children[index],
                    frame_path + [index],
                )
            )

    logger.debug(
        "Execution frame extraction completed: "
        "transactionHash=%s frames=%s",
        tx_hash,
        len(records),
    )

    return records
