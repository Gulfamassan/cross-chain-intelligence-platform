"""
Performance API Routes

Ye module system ki performance metrics (response times, cache
stats) dikhane ka endpoint handle karta hai.
"""

from fastapi import APIRouter

from performance.timer import performance_timer
from performance.cache import simple_cache
from performance.neo4j_indexes import neo4j_index_manager

# Router banate hain jo main.py mein include hoga
router = APIRouter()


@router.get("/performance/stats")
def get_performance_stats():
    """
    System ki performance statistics deta hai — average times
    har major operation ke liye, aur cache stats.

    Returns:
        dict: Performance metrics
    """
    return {
        "average_times_seconds": performance_timer.get_all_averages(),
        "cache_stats": simple_cache.get_stats(),
    }


@router.post("/performance/setup-indexes")
def setup_neo4j_indexes():
    """
    Neo4j database par performance indexes create karta hai.

    Returns:
        dict: Confirmation message
    """
    return neo4j_index_manager.create_all_indexes()