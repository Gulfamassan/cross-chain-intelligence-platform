"""
Simple In-Memory Cache

Ye module ek basic caching system deta hai — expensive results
(jaise embeddings, risk analysis) ko memory mein temporarily store
karta hai, taake same input ke liye dobara calculation na karni pade.
"""

import time


class SimpleCache:
    """
    Ye class ek simple key-value cache hai, jisme har entry ka
    apna expiry time hota hai (taake purana/stale data use na ho).
    """

    def __init__(self, default_ttl_seconds: int = 300):
        """
        Args:
            default_ttl_seconds (int): Kitni der tak ek entry valid rahegi
                                        (default 5 minutes)
        """
        self.store = {}
        self.default_ttl = default_ttl_seconds

    def get(self, key: str):
        """
        Cache se value nikalta hai, agar expire na hui ho.

        Args:
            key (str): Cache key

        Returns:
            Value agar mile aur expire na hui ho, warna None
        """
        if key not in self.store:
            return None

        value, expiry_time = self.store[key]

        if time.time() > expiry_time:
            # Expire ho chuki hai, cache se hata dete hain
            del self.store[key]
            return None

        return value

    def set(self, key: str, value, ttl_seconds: int = None):
        """
        Cache mein ek value store karta hai, expiry time ke saath.

        Args:
            key (str): Cache key
            value: Store karne wali value
            ttl_seconds (int): Kitni der tak valid rahegi (optional, default use hoga)
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expiry_time = time.time() + ttl
        self.store[key] = (value, expiry_time)

    def clear(self):
        """
        Poora cache khaali kar deta hai.
        """
        self.store.clear()

    def get_stats(self) -> dict:
        """
        Cache ki basic statistics deta hai.

        Returns:
            dict: Kitni entries hain cache mein
        """
        return {
            "total_cached_entries": len(self.store),
        }


# Ek single instance banate hain jo poore project mein import hoga
simple_cache = SimpleCache()