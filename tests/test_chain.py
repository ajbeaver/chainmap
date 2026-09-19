from modules.chain import generate_chain_data
from modules.normalize import normalize_rpc_data


def test_chain_data_matches_rpc_observations(w3):
    expected_client_version = w3.client_version
    expected_chain_id = w3.eth.chain_id
    expected_block_number = w3.eth.block_number
    expected_syncing = normalize_rpc_data(
        w3.eth.syncing
    )

    data = generate_chain_data(w3)

    assert data == {
        "client_version": expected_client_version,
        "chain_id": expected_chain_id,
        "block_number": expected_block_number,
        "syncing": expected_syncing,
    }


def test_chain_data_contains_only_observed_fields(w3):
    data = generate_chain_data(w3)

    assert set(data) == {
        "client_version",
        "chain_id",
        "block_number",
        "syncing",
    }


def test_chain_id_is_anvil_chain(w3):
    data = generate_chain_data(w3)

    assert data["chain_id"] == 31337


def test_chain_syncing_preserves_rpc_value(w3):
    data = generate_chain_data(w3)

    assert data["syncing"] == normalize_rpc_data(
        w3.eth.syncing
    )
