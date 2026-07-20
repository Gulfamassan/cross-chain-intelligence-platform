"""
Wallet Profile

Ye module ek WalletProfile class define karta hai jo kisi bhi
wallet ki saari nikali gayi features ko ek organized object mein
store karta hai.
"""


class WalletProfile:
    """
    Ek wallet ki poori "personality" (behavior profile) is class mein
    store hoti hai — basic info, activity, financial, network, aur time
    se related features.
    """

    def __init__(self, wallet_address: str, chain: str):
        """
        Naya wallet profile banate hain — pehle sab kuch khaali/default hota hai.

        Args:
            wallet_address (str): Wallet ka address
            chain (str): Blockchain ka naam
        """
        # Basic
        self.wallet_address = wallet_address
        self.chain = chain
        self.first_transaction = None
        self.last_transaction = None

        # Activity
        self.total_transactions = 0
        self.sent_transactions = 0
        self.received_transactions = 0

        # Financial
        self.total_sent_eth = 0.0
        self.total_received_eth = 0.0
        self.average_transaction_value = 0.0
        self.max_transaction_value = 0.0
        self.min_transaction_value = 0.0

        # Network
        self.unique_senders = 0
        self.unique_receivers = 0
        self.total_unique_contacts = 0

        # Time
        self.active_days = 0
        self.average_transactions_per_day = 0.0

        # Future Features (Abhi Placeholder)
        self.bridge_usage = False
        self.smart_contract_usage = False
        self.token_diversity = 0
        self.dex_interaction = False
        self.nft_activity = False
        self.mixing_services = False
        self.stablecoin_ratio = 0.0

    def to_dict(self) -> dict:
        """
        Poore profile ko ek dictionary (JSON-jaisa) format mein deta hai,
        taake API response mein ya CSV mein use kiya ja sake.

        Returns:
            dict: Wallet ka poora feature profile
        """
        return {
            # Basic
            "wallet_address": self.wallet_address,
            "chain": self.chain,
            "first_transaction": str(self.first_transaction) if self.first_transaction else None,
            "last_transaction": str(self.last_transaction) if self.last_transaction else None,

            # Activity
            "total_transactions": self.total_transactions,
            "sent_transactions": self.sent_transactions,
            "received_transactions": self.received_transactions,

            # Financial
            "total_sent_eth": float(self.total_sent_eth),
"total_received_eth": float(self.total_received_eth),
"average_transaction_value": float(self.average_transaction_value),
"max_transaction_value": float(self.max_transaction_value),
"min_transaction_value": float(self.min_transaction_value),

            # Network
            "unique_senders": self.unique_senders,
            "unique_receivers": self.unique_receivers,
            "total_unique_contacts": self.total_unique_contacts,

            # Time
            "active_days": self.active_days,
            "average_transactions_per_day": self.average_transactions_per_day,

            # Future Features
            "bridge_usage": self.bridge_usage,
            "smart_contract_usage": self.smart_contract_usage,
            "token_diversity": self.token_diversity,
            "dex_interaction": self.dex_interaction,
            "nft_activity": self.nft_activity,
            "mixing_services": self.mixing_services,
            "stablecoin_ratio": self.stablecoin_ratio,
        }