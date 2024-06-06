from connectrum.client import StratumClient
from connectrum.svr_info import ServerInfo


class Connection:
    def __init__(self, host: str, port: int, protocol: str):

        # avoid calls to connectrum here that may create additional event loops

        self.client = None
        ports = (protocol + str(port)) if port else protocol

        self.server_info = ServerInfo(host, host, ports=ports)
        self.protocol = protocol

    async def connect(self):
        self.client = StratumClient()

        connector = self.client.connect(self.server_info, self.protocol, use_tor=False, disable_cert_verify=False, short_term=True)
        await connector

    async def close(self):
        self.client.close()

