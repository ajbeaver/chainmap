import argparse
import json
import logging

from modules.orchestration import (
    create_chainmap_for_rpc,
    ingest_transaction,
)
from modules.rpc import connect_rpc


APP_NAME = "chainmap"
VERSION = "v0.0.1-beta.1"

LIBRARY_LOGGERS = [
    "web3",
    "urllib3",
]


logger = logging.getLogger(__name__)


def setup_logging(verbosity=0):
    levels = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
        3: logging.DEBUG,
    }

    level = levels.get(
        min(verbosity, 3),
        logging.DEBUG,
    )

    logging.basicConfig(
        level=level,
        format=(
            "%(asctime)s - %(name)s - "
            "%(levelname)s - %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    for name in LIBRARY_LOGGERS:
        if verbosity < 3:
            logging.getLogger(
                name
            ).setLevel(
                logging.WARNING
            )

        else:
            logging.getLogger(
                name
            ).setLevel(
                logging.NOTSET
            )


def build_parser():
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description=(
            "Build an evidence-backed relationship "
            "map from Ethereum transactions."
        ),
    )

    parser.add_argument(
        "--rpc",
        required=True,
        help=(
            "Ethereum HTTP/HTTPS RPC endpoint"
        ),
    )

    parser.add_argument(
        "transactions",
        nargs="+",
        metavar="TX_HASH",
        help=(
            "Transaction hash to ingest. "
            "Multiple hashes may be supplied."
        ),
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(
        args.verbose
    )

    logger.info(
        "Starting ChainMap"
    )

    w3 = connect_rpc(
        args.rpc
    )

    chain_map = (
        create_chainmap_for_rpc(
            w3
        )
    )

    logger.info(
        "Created map for chain ID %s",
        chain_map["chain_id"],
    )

    for tx_hash in args.transactions:
        logger.info(
            "Processing transaction: %s",
            tx_hash,
        )

        ingest_transaction(
            w3,
            chain_map,
            tx_hash,
        )

    print(
        json.dumps(
            chain_map,
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
