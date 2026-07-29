"""
Performance Timer

Ye module functions/endpoints ka execution time measure karta hai,
aur recent measurements ko memory mein store karta hai — taake
hum dekh sakein average response times kya hain.
"""

import time
import functools


class PerformanceTimer:
    """
    Ye class execution times track karti hai har operation ke liye.
    """

    def __init__(self):
        self.records = {}

    def record(self, operation_name: str, duration_seconds: float):
        """
        Ek operation ka duration store karta hai.
        """
        if operation_name not in self.records:
            self.records[operation_name] = []
        self.records[operation_name].append(duration_seconds)

        # Sirf recent 50 measurements rakhte hain (memory bachane ke liye)
        if len(self.records[operation_name]) > 50:
            self.records[operation_name] = self.records[operation_name][-50:]

    def get_average(self, operation_name: str) -> float:
        """
        Diye gaye operation ka average time deta hai.
        """
        if operation_name not in self.records or not self.records[operation_name]:
            return 0.0
        values = self.records[operation_name]
        return round(sum(values) / len(values), 4)

    def get_all_averages(self) -> dict:
        """
        Saare tracked operations ke average times deta hai.
        """
        return {name: self.get_average(name) for name in self.records}

    def timed(self, operation_name: str):
        """
        Ek decorator jo kisi bhi function ko "wrap" kar ke uska
        time automatically measure aur record kar deta hai.

        Usage:
            @performance_timer.timed("graph_build")
            def build_graph(...):
                ...
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start
                self.record(operation_name, duration)
                return result
            return wrapper
        return decorator


# Ek single instance banate hain jo poore project mein import hoga
performance_timer = PerformanceTimer()