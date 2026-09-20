from modules.transaction import (
    generate_transaction_data,
)
from modules.config import (
    build_chainmap_trace_options,
)
from modules.execution import (
    extract_execution_frames,
)
from modules.map import (
    create_map,
    ingest_relationships,
)
from modules.relationships import (
    extract_relationships,
)
from modules.trace import generate_trace_data


def create_chainmap_for_rpc(w3):
    chain_id = w3.eth.chain_id

    return create_map(
        chain_id
    )


def ingest_transaction(
    w3,
    chain_map,
    tx_hash,
):
    rpc_chain_id = w3.eth.chain_id

    if (
        chain_map["chain_id"]
        != rpc_chain_id
    ):
        raise ValueError(
            "Chain map chain_id does not "
            "match RPC chain_id"
        )

    generate_transaction_data(
        w3,
        tx_hash,
    )

    trace_data = generate_trace_data(
        w3,
        tx_hash,
        build_chainmap_trace_options(),
    )

    execution_records = (
        extract_execution_frames(
            trace_data,
            tx_hash,
        )
    )

    relationships = extract_relationships(
        execution_records
    )

    ingest_relationships(
        chain_map,
        relationships,
    )

    return chain_map
