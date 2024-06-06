import asyncio, argparse
import logging
import time
import json
from decimal import Decimal

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from connectrum import ElectrumErrorResponse

from connectrum.client import StratumClient
from connection import Connection
from collections import deque

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z"
)

logging.getLogger('connectrum').setLevel(level=logging.WARN)


def create_rpc_connection(rpc_host: str, rpc_port: int, rpc_user: str, rpc_password: str) -> AuthServiceProxy:
    connection_string = f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}"

    logging.info(f"Connecting to bitcoin core rpc {rpc_host}:{rpc_port} as '{rpc_user}'")

    rpc_connection = AuthServiceProxy(connection_string)

    return rpc_connection


def get_bitcoin_core_mempool(rpc_host: str, rpc_port: int, rpc_user: str, rpc_password: str) -> dict:
    rpc_connection = create_rpc_connection(rpc_host, rpc_port, rpc_user, rpc_password)

    logging.info("calling getrawmempool(verbose=True)")

    start_time = time.time()
    mempool = rpc_connection.getrawmempool(True)
    time_to_retrieve = time.time() - start_time

    logging.info(f"retrieved {len(mempool)} mempool transactions in {time_to_retrieve:.1f} seconds")

    return mempool


class TransactionCounter:
    def __init__(self, client: StratumClient):
        self.client = client

        self.attempted_count = 0
        self.retrieved_count = 0

        self.missing = []

    async def get_tx_from_electrum(self, tx: str):
        try:
            self.attempted_count += 1
            transaction = await self.client.RPC('blockchain.transaction.get', tx)
            self.retrieved_count += 1
        except ElectrumErrorResponse as e:
            self.missing.append(tx)


class CoroQueue:
    """
    Schedules async tasks to run from a queue, keeping the number of concurrent tasks running_count.
    """
    def __init__(self, running_count=1000):
        self.task_count = running_count
        self.running = set()
        self.waiting = deque()

    @property
    def running_task_count(self):
        return len(self.running)

    def add_task(self, coro):
        if len(self.running) >= self.task_count:
            self.waiting.append(coro)
        else:
            self._start_task(coro)

    def _start_task(self, coro):
        self.running.add(coro)
        asyncio.create_task(self._task(coro))

    async def _task(self, coro):
        try:
            return await coro
        finally:
            self.running.remove(coro)
            if self.waiting:
                next_coro = self.waiting.popleft()
                self._start_task(next_coro)


# Custom JSON encoder to handle Decimal
# objects
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # Or float(obj) if you prefer
        return super(DecimalEncoder, self).default(obj)


def display_missing_transactions(missing: list, mempool: dict):
    for tx in missing:
        transaction = mempool[tx]
        age = transaction['time'] - time.time()
        print(f"{age} {mempool[tx]}")


async def check_bitcoin_mempool_is_known_by_electrs(bitcoin_core_mempool: dict, connection: Connection):

    await connection.connect()

    runner = CoroQueue()

    counter = TransactionCounter(connection.client)

    logging.info(f"retrieving transactions from electrs using blockchain.transaction.get")

    for tx in bitcoin_core_mempool.keys():
        runner.add_task(counter.get_tx_from_electrum(tx))

    while runner.running_task_count > 0:
        await asyncio.sleep(5)
        missing_count = len(counter.missing)
        missing_fraction = missing_count / (counter.retrieved_count + 0.0 if counter.retrieved_count > 0 else 1.0)
        logging.info(f"retrieved={counter.retrieved_count} pending={len(runner.waiting)} missing={len(counter.missing)} ({missing_fraction:.8f}%)")

    await connection.close()

    display_missing_transactions(counter.missing, bitcoin_core_mempool)


def main():

    parser = argparse.ArgumentParser(description='compare bitcoin core mempool with electrum mempool')

    parser.add_argument('--electrum-host', default='localhost',
                        help='Hostname of Electrum server to use')
    parser.add_argument('--electrum-transport-protocol', default='t',
                        help='Electrum server transport protocol code: t=TCP Cleartext, s=SSL, etc')
    parser.add_argument('--electrum-port', default=50001,
                        help='Port number to override default for protocol')

    parser.add_argument('--bitcoin-rpc-host', default='localhost',
                        help='Hostname of bitcoin core rpc server')
    parser.add_argument('--bitcoin-rpc-port', default=8332,
                        help='Port of bitcoin core rpc server')
    parser.add_argument('--bitcoin-rpc-user', default='rpcuser',
                        help='username of bitcoin core rpc server')
    parser.add_argument('--bitcoin-rpc-password', default='rpcpassword',
                        help='username of bitcoin core rpc server')

    args = parser.parse_args()

    bitcoin_core_mempool = get_bitcoin_core_mempool(rpc_host=args.bitcoin_rpc_host,
                                       rpc_port=int(args.bitcoin_rpc_port),
                                       rpc_user=args.bitcoin_rpc_user,
                                       rpc_password=args.bitcoin_rpc_password)

    electrum_connection = Connection(host=args.electrum_host,
                                     port=args.electrum_port,
                                     protocol=args.electrum_transport_protocol)

    asyncio.run(check_bitcoin_mempool_is_known_by_electrs(bitcoin_core_mempool, electrum_connection))


if __name__ == '__main__':
    main()
