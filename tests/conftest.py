import json
import shutil
import socket
import subprocess
import time

import pytest
import requests

from modules.rpc import connect_rpc


ACCOUNT_0 = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
ACCOUNT_1 = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

UNKNOWN_HASH = "0x" + "11" * 32
TOPIC_0 = "0x" + "22" * 32


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def rpc_call(url, method, params=None):
    response = requests.post(
        url,
        json={
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1,
        },
        timeout=3,
    )

    response.raise_for_status()
    payload = response.json()

    if "error" in payload:
        raise RuntimeError(
            f"{method} failed: {json.dumps(payload['error'])}"
        )

    return payload.get("result")


def wait_for_rpc(url, timeout=10):
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            if rpc_call(url, "web3_clientVersion"):
                return

        except Exception:
            time.sleep(0.1)

    raise RuntimeError(f"RPC failed to start at {url}")


def wait_for_receipt(url, tx_hash, timeout=10):
    deadline = time.time() + timeout

    while time.time() < deadline:
        receipt = rpc_call(
            url,
            "eth_getTransactionReceipt",
            [tx_hash],
        )

        if receipt is not None:
            return receipt

        time.sleep(0.05)

    raise RuntimeError(
        f"Timed out waiting for receipt: {tx_hash}"
    )


def send_transaction(url, transaction):
    tx_hash = rpc_call(
        url,
        "eth_sendTransaction",
        [transaction],
    )

    wait_for_receipt(url, tx_hash)

    return tx_hash


def build_call_runtime(address):
    target = address.removeprefix("0x")

    if len(target) != 40:
        raise ValueError(
            "Call target must be a 20-byte address"
        )

    return (
        "6000"  # return size
        "6000"  # return offset
        "6000"  # input size
        "6000"  # input offset
        "6000"  # value
        f"73{target}"  # target address
        "61ffff"  # gas
        "f1"  # CALL
        "00"  # STOP
    )
    
    
def deploy_runtime(url, runtime_hex):
    runtime_hex = runtime_hex.removeprefix("0x")
    length = len(bytes.fromhex(runtime_hex))

    if length > 255:
        raise ValueError(
            "Test runtime must fit in PUSH1 init code"
        )

    init_code = (
        f"60{length:02x}"
        "600c"
        "6000"
        "39"
        f"60{length:02x}"
        "6000"
        "f3"
        f"{runtime_hex}"
    )

    tx_hash = rpc_call(
        url,
        "eth_sendTransaction",
        [
            {
                "from": ACCOUNT_0,
                "data": f"0x{init_code}",
                "gas": hex(1_000_000),
            }
        ],
    )

    receipt = wait_for_receipt(url, tx_hash)

    return receipt["contractAddress"], tx_hash


@pytest.fixture(scope="session")
def anvil_url():
    anvil = shutil.which("anvil")

    if anvil is None:
        pytest.fail(
            "anvil is not installed or available in PATH"
        )

    port = free_port()
    url = f"http://127.0.0.1:{port}"

    process = subprocess.Popen(
        [
            anvil,
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--chain-id",
            "31337",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        wait_for_rpc(url)
        yield url

    finally:
        process.terminate()

        try:
            process.wait(timeout=3)

        except subprocess.TimeoutExpired:
            process.kill()


@pytest.fixture(scope="session")
def w3(anvil_url):
    return connect_rpc(anvil_url)


@pytest.fixture(scope="session")
def chain_state(anvil_url):
    legacy_tx_hash = send_transaction(
        anvil_url,
        {
            "from": ACCOUNT_0,
            "to": ACCOUNT_1,
            "value": hex(10**18),
            "gas": hex(21_000),
            "gasPrice": hex(1_000_000_000),
        },
    )

    eip1559_tx_hash = send_transaction(
        anvil_url,
        {
            "from": ACCOUNT_0,
            "to": ACCOUNT_1,
            "value": hex(12345),
            "gas": hex(21_000),
            "maxFeePerGas": hex(2_000_000_000),
            "maxPriorityFeePerGas": hex(1_000_000_000),
        },
    )

    log_runtime = (
        f"7f{TOPIC_0[2:]}"
        "6000"
        "6000"
        "a1"
        "00"
    )

    log_contract, deploy_log_tx_hash = deploy_runtime(
        anvil_url,
        log_runtime,
    )

    log_tx_hash = send_transaction(
        anvil_url,
        {
            "from": ACCOUNT_0,
            "to": log_contract,
            "gas": hex(100_000),
        },
    )

    leaf_contract, _ = deploy_runtime(
        anvil_url,
        "00",
    )

    middle_contract, _ = deploy_runtime(
        anvil_url,
        build_call_runtime(
            leaf_contract
        ),
    )

    caller_contract, _ = deploy_runtime(
        anvil_url,
        build_call_runtime(
            middle_contract
        ),
    )

    nested_call_tx_hash = send_transaction(
        anvil_url,
        {
            "from": ACCOUNT_0,
            "to": caller_contract,
            "gas": hex(250_000),
        },
    )

    latest_block = rpc_call(
        anvil_url,
        "eth_getBlockByNumber",
        ["latest", False],
    )

    return {
        "legacy_tx_hash": legacy_tx_hash,
        "eip1559_tx_hash": eip1559_tx_hash,
        "log_contract": log_contract,
        "log_tx_hash": log_tx_hash,
        "deploy_log_tx_hash": deploy_log_tx_hash,
        "leaf_contract": leaf_contract,
        "middle_contract": middle_contract,
        "caller_contract": caller_contract,
        "nested_call_tx_hash": nested_call_tx_hash,
        "latest_block_number": int(
            latest_block["number"],
            16,
        ),
        "latest_block_hash": latest_block["hash"],
    }
