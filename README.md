# ChainMap 

**UNDER DEVELOPMENT**

ChainMap reconstructs and continuously updates the relationships between Ethereum entities from observable on-chain evidence.

Rather than treating blocks, transactions, receipts, traces, and addresses as isolated objects, ChainMap is designed to preserve the evidence that connects them and build a longer-lived map of how an Ethereum environment behaves over time.

## Overview

Most block explorers are optimized for inspecting one object at a time: a transaction, an address, a block, or a contract.

ChainMap is focused on the relationships between those objects.

The project collects Ethereum data directly from an RPC endpoint, preserves that data with minimal transformation, reconstructs transaction execution from traces, extracts directly observed relationships between entities, and accumulates those observations into a chain-scoped map.

The long-term goal is lifecycle visibility across four domains:

- **Origin** — where an entity came from, including creation mechanism, transaction, and surrounding evidence.
- **Execution** — what actually happened during transaction execution, including nested calls, contract creation, value, and events.
- **Relationships** — which entities directly interacted and what evidence supports each observed connection.
- **Change** — how entities and relationships appear, disappear, or change over time.

ChainMap is intended for developers, operators, researchers, and investigators who need relationship-oriented Ethereum data without hiding the underlying evidence behind labels or inferred semantics.

## Design Principles

ChainMap treats RPC responses, receipts, traces, logs, and execution frames as evidence.

Shared primitives normalize representation where necessary, but avoid semantic interpretation. Bytes become `0x...` strings, mappings become dictionaries, and tuple-like collections become lists. The primitives do not classify contracts, rename canonical RPC fields, infer intent, or summarize away source data.

Derived layers remain evidence-backed. A relationship means ChainMap directly observed one execution frame connecting two entities. The map correlates those observations over time, but does not decide that one entity owns, controls, depends on, or is otherwise semantically related to another.

Every higher-level observation is intended to remain traceable back to the transaction and execution frame that produced it.

## Features

- HTTP/HTTPS Ethereum JSON-RPC connectivity with endpoint sanitization for logs.
- Chain, block, transaction, receipt, and address-state collection through Web3.py.
- Generic `debug_traceTransaction` access without forcing a tracer configuration.
- Recursive `callTracer` execution extraction with deterministic frame paths.
- Direct relationship extraction from execution frames while preserving complete local frame evidence.
- Chain-scoped maps that correlate repeated address-to-address observations.
- Idempotent map ingestion using transaction hash and frame path as the observation coordinate.
- Canonical address identity for map keys while preserving the original observed address representation in evidence.
- Atomic relationship-batch ingestion so malformed input cannot partially mutate map state.
- No ABI decoding, semantic classification, graph scoring, or presentation-layer inference in the core pipeline.

## Current Implementation

The current implementation establishes the factual data pipeline from an Ethereum RPC endpoint through long-lived correlated map state:

```text
Ethereum RPC
    ↓
rpc / chain / block / transaction / receipt / address / trace
    ↓
normalized source evidence
    ↓
execution
    ↓
relationships
    ↓
map
```

The implemented modules currently provide:

- **RPC connection and validation** — validates HTTP/HTTPS endpoints, creates a Web3 connection, verifies the endpoint through `web3_clientVersion`, and sanitizes potentially sensitive endpoint data before logging.
- **Normalization** — recursively converts bytes to hexadecimal strings and RPC mapping/sequence objects into ordinary Python structures without selecting or renaming fields.
- **Chain data** — collects client version, chain ID, current block number, and sync state as independent observations.
- **Block data** — returns the normalized complete Web3 block response for any block identifier supported by Web3.py.
- **Transaction data** — validates a transaction hash and returns the normalized complete transaction response.
- **Receipt data** — returns the normalized complete transaction receipt without mixing in transaction data or interpreting receipt status.
- **Address data** — collects balance, transaction count, and bytecode at a caller-selected block identifier.
- **Trace data** — exposes `debug_traceTransaction` and returns the normalized RPC result. Tracer options are caller-controlled.
- **Execution extraction** — converts a `callTracer` tree into ordered execution records while preserving each frame's location using paths such as `[0]`, `[0, 0]`, and `[0, 0, 0]`.
- **Relationship extraction** — converts graphable execution frames into directed `from → to` observations and retains the complete local frame as evidence.
- **Map construction** — accumulates relationship observations into a long-lived, chain-scoped Python object with canonical address keys, directed edges, evidence retention, idempotent re-ingestion, and conflict detection.

The map is intentionally still factual rather than inferential. It records what has been observed and how those observations connect. It does not yet attempt to label protocols, infer ownership or dependency, decode ABIs, score entities, or determine higher-level meaning.

Lifecycle chronology is also not yet complete. Relationship observations currently carry transaction hash and execution frame path, but not enough block-position metadata to truthfully calculate concepts such as first seen or last seen across independently processed transactions.

The CLI in `main.py` is currently a skeleton. The implemented API modules are tested independently and in composition, but the complete transaction-to-map pipeline has not yet been wired into the command-line entry point.

## Requirements

- Python 3.11 or newer
- Web3.py 8 or newer
- Requests 2 or newer
- An Ethereum JSON-RPC endpoint with `debug_traceTransaction` support for trace-based execution and relationship collection
- Foundry Anvil for the integration test suite

## Installation

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/ajbeaver/chainmap.git
cd chainmap

python3 -m venv .venv
source .venv/bin/activate
```

Install the project with development dependencies:

```bash
python3 -m pip install -e '.[dev]'
```

For runtime use without the test dependencies:

```bash
python3 -m pip install -e .
```

## Usage

The command-line interface is not wired to the data pipeline yet. The current implementation is usable directly as a Python API.

A minimal transaction-to-map flow looks like:

```python
from modules.rpc import connect_rpc
from modules.transaction import generate_transaction_data
from modules.trace import generate_trace_data
from modules.execution import extract_execution_frames
from modules.relationships import extract_relationships
from modules.map import create_map, ingest_relationships


rpc_url = "http://127.0.0.1:8545"
tx_hash = "0xYOUR_32_BYTE_TRANSACTION_HASH"

w3 = connect_rpc(rpc_url)

# Establish the transaction as an independent source observation.
transaction = generate_transaction_data(
    w3,
    tx_hash,
)

trace = generate_trace_data(
    w3,
    tx_hash,
    {
        "tracer": "callTracer",
        "tracerConfig": {
            "withLog": True,
        },
    },
)

execution = extract_execution_frames(
    trace,
    tx_hash,
)

relationships = extract_relationships(
    execution,
)

chain_map = create_map(
    w3.eth.chain_id,
)

ingest_relationships(
    chain_map,
    relationships,
)
```

The resulting `chain_map` is an ordinary Python dictionary containing canonical node identities, directed edges, and the observations supporting those edges.

## Configuration

ChainMap does not currently require a configuration file or environment variables.

RPC endpoints are supplied by the caller:

```python
w3 = connect_rpc("https://YOUR_RPC_ENDPOINT")
```

The current RPC connector intentionally supports HTTP and HTTPS endpoints only.

Trace support depends on the connected Ethereum client and RPC provider. Relationship extraction expects `callTracer`-shaped trace data, while the lower-level trace primitive itself remains tracer-agnostic.

## Project Structure

```text
chainmap/
├── main.py
├── modules/
│   ├── address.py
│   ├── block.py
│   ├── chain.py
│   ├── execution.py
│   ├── map.py
│   ├── normalize.py
│   ├── receipt.py
│   ├── relationships.py
│   ├── rpc.py
│   ├── trace.py
│   ├── transaction.py
│   └── validation.py
├── tests/
├── pyproject.toml
└── README.md
```

The current layers are intentionally separated:

```text
collection primitives
→ execution structure
→ relationship observations
→ accumulated map state
```

`main.py` is reserved for orchestration rather than implementing the behavior of those layers directly.

## Development

Install the development dependencies:

```bash
python3 -m pip install -e '.[dev]'
```

Run the complete test suite:

```bash
python3 -m pytest -v
```

The integration tests start a local Anvil node and exercise the same RPC, tracing, execution, relationship, and map paths used by the project.

The project currently favors small modules, explicit validation, minimal dependencies, source-evidence preservation, and tests that compare wrapper output directly with Web3 or JSON-RPC output where practical.

## Project Status

**Early alpha.**

The acquisition, normalization, execution, relationship, and in-memory map layers are implemented and covered by the current test suite.

The next phase is focused on hardening the API boundaries and wiring the existing modules into the first complete orchestration path. Persistence, lifecycle chronology, higher-level reasoning, and presentation are intentionally later concerns.

## License

Licensed under the MIT License.

See `LICENSE` for details.
