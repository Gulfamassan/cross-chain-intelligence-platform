"""
Chain Manager

Ye poore software ka "traffic controller" hai.
User jab kisi bhi blockchain ka naam bhejta hai (jaise "ethereum"),
ye us blockchain ka sahi collector dhoondh ke deta hai.

Ye pattern future mein naye blockchains add karna bahut aasan banata hai -
bas naya collector banao aur yahan register kar do.
"""

from blockchain.collectors.ethereum_collector import EthereumCollector


class ChainManager:
    """
    Ye class saare blockchain collectors ko manage karti hai.
    """

    def __init__(self):
        """
        Saare available collectors ko yahan register karte hain.
        Jaise-jaise naye collectors banenge (Polygon, BNB, etc.),
        unhe is dictionary mein add karte jayenge.
        """
        self.collectors = {
            "ethereum": EthereumCollector(),
            # "polygon": PolygonCollector(),      -> future mein add hoga
            # "bnb": BNBCollector(),               -> future mein add hoga
            # "tron": TronCollector(),             -> future mein add hoga
            # "arbitrum": ArbitrumCollector(),     -> future mein add hoga
            # "optimism": OptimismCollector(),     -> future mein add hoga
            # "avalanche": AvalancheCollector(),   -> future mein add hoga
        }

    def get_collector(self, chain: str):
        """
        Diye gaye blockchain naam ka collector deta hai.

        Args:
            chain (str): Blockchain ka naam, jaise "ethereum"

        Returns:
            BaseCollector: Us blockchain ka collector object

        Raises:
            ValueError: Agar wo blockchain support nahi hoti
        """
        chain = chain.lower()

        if chain not in self.collectors:
            raise ValueError(
                f"Unsupported blockchain: '{chain}'. "
                f"Supported chains: {list(self.collectors.keys())}"
            )

        return self.collectors[chain]


# Ek single instance banate hain jo poore project mein import hoga
chain_manager = ChainManager()