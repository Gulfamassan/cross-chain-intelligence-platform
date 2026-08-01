"""
Performance API Routes

Handles displaying system performance metrics (response times,
cache stats).
"""

from fastapi import APIRouter

from performance.timer import performance_timer
from performance.cache import simple_cache
from performance.neo4j_indexes import neo4j_index_manager

router = APIRouter()


@router.get("/performance/stats")
def get_performance_stats():
    """
    Returns the system's performance statistics — average times for
    each major operation, and cache stats.

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
    Creates performance indexes on the Neo4j database.

    Returns:
        dict: Confirmation message
    """
    return neo4j_index_manager.create_all_indexes()