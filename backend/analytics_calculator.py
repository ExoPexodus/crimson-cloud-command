from sqlalchemy import func, and_, desc, distinct, cast, Date
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any
from models import Node, Pool, PoolAnalytics, NodeStatus
import logging

logger = logging.getLogger(__name__)

class DashboardAnalyticsCalculator:
    """
    Dedicated calculator for dashboard analytics.
    Each method calculates a specific metric shown on the main dashboard.
    """
    
    @staticmethod
    def get_active_pools_24h(db: Session) -> int:
        """
        Count distinct pools active in the last 24 hours.
        A pool is considered active if it has analytics data in the last 24h with is_active=True.
        """
        try:
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            
            count = db.query(func.count(distinct(PoolAnalytics.pool_id))).filter(
                PoolAnalytics.timestamp >= twenty_four_hours_ago,
                PoolAnalytics.is_active == True
            ).scalar()
            
            return count or 0
        except Exception as e:
            logger.error(f"Error calculating active pools (24h): {str(e)}")
            return 0
    
    @staticmethod
    def get_max_pools_today(db: Session) -> int:
        """
        Maximum number of distinct pools active at any point today (since midnight).
        Groups by hour and finds the hour with the most distinct active pools.
        """
        try:
            # Get start of today (midnight)
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Group by hour and count distinct pools per hour
            hourly_counts = db.query(
                func.date_trunc('hour', PoolAnalytics.timestamp).label('hour'),
                func.count(distinct(PoolAnalytics.pool_id)).label('pool_count')
            ).filter(
                PoolAnalytics.timestamp >= today_start,
                PoolAnalytics.is_active == True
            ).group_by(
                func.date_trunc('hour', PoolAnalytics.timestamp)
            ).all()
            
            if not hourly_counts:
                return 0
            
            # Return the maximum pool count from any hour
            max_count = max([row.pool_count for row in hourly_counts])
            return max_count
        except Exception as e:
            logger.error(f"Error calculating max pools today: {str(e)}")
            return 0
    
    @staticmethod
    def get_peak_instances_24h(db: Session) -> int:
        """
        Maximum total instances running simultaneously across all pools in the last 24 hours.
        Groups by 5-minute intervals and sums current_instances across all pools.
        Returns the highest sum found.
        """
        try:
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            
            # For each distinct timestamp (or 5-min interval), get the sum of current_instances
            # We'll use subquery to get latest record per pool per 5-min interval
            subquery = db.query(
                func.date_trunc('minute', PoolAnalytics.timestamp).label('interval'),
                PoolAnalytics.pool_id,
                func.max(PoolAnalytics.current_instances).label('max_instances')
            ).filter(
                PoolAnalytics.timestamp >= twenty_four_hours_ago
            ).group_by(
                func.date_trunc('minute', PoolAnalytics.timestamp),
                PoolAnalytics.pool_id
            ).subquery()
            
            # Sum instances across all pools per interval
            interval_sums = db.query(
                subquery.c.interval,
                func.sum(subquery.c.max_instances).label('total_instances')
            ).group_by(
                subquery.c.interval
            ).all()
            
            if not interval_sums:
                return 0
            
            # Return the maximum total from any interval
            peak = max([row.total_instances for row in interval_sums])
            return int(peak) if peak else 0
        except Exception as e:
            logger.error(f"Error calculating peak instances (24h): {str(e)}")
            return 0
    
    @staticmethod
    def get_current_running_instances(db: Session) -> int:
        """
        Total instances currently running across all active pools.
        Gets the latest analytics record for each pool from nodes that are online (heartbeat within 5 min).
        """
        try:
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            
            # Subquery to get the latest analytics record for each pool
            latest_analytics_subquery = db.query(
                PoolAnalytics.pool_id,
                func.max(PoolAnalytics.timestamp).label('max_timestamp')
            ).filter(
                PoolAnalytics.timestamp >= five_minutes_ago
            ).group_by(
                PoolAnalytics.pool_id
            ).subquery()
            
            # Join to get the full records and sum current_instances
            # Also ensure the node is active
            total = db.query(
                func.sum(PoolAnalytics.current_instances)
            ).join(
                latest_analytics_subquery,
                and_(
                    PoolAnalytics.pool_id == latest_analytics_subquery.c.pool_id,
                    PoolAnalytics.timestamp == latest_analytics_subquery.c.max_timestamp
                )
            ).join(
                Node,
                PoolAnalytics.node_id == Node.id
            ).filter(
                Node.last_heartbeat >= five_minutes_ago,
                Node.status == NodeStatus.ACTIVE
            ).scalar()
            
            return int(total) if total else 0
        except Exception as e:
            logger.error(f"Error calculating current running instances: {str(e)}")
            return 0
    
    @staticmethod
    def get_active_nodes(db: Session) -> int:
        """
        Count of nodes with recent heartbeats (within last 5 minutes) and status ACTIVE.
        """
        try:
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            
            count = db.query(func.count(Node.id)).filter(
                Node.last_heartbeat >= five_minutes_ago,
                Node.status == NodeStatus.ACTIVE
            ).scalar()
            
            return count or 0
        except Exception as e:
            logger.error(f"Error calculating active nodes: {str(e)}")
            return 0
    
    @staticmethod
    def get_avg_system_metrics(db: Session) -> Dict[str, float]:
        """
        Average CPU and memory utilization across all active pools.
        Gets the latest analytics record for each pool and averages the metrics.
        """
        try:
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            
            # Subquery to get the latest analytics record for each pool
            latest_analytics_subquery = db.query(
                PoolAnalytics.pool_id,
                func.max(PoolAnalytics.timestamp).label('max_timestamp')
            ).filter(
                PoolAnalytics.timestamp >= five_minutes_ago
            ).group_by(
                PoolAnalytics.pool_id
            ).subquery()
            
            # Get the latest records
            latest_records = db.query(
                PoolAnalytics.avg_cpu_utilization,
                PoolAnalytics.avg_memory_utilization
            ).join(
                latest_analytics_subquery,
                and_(
                    PoolAnalytics.pool_id == latest_analytics_subquery.c.pool_id,
                    PoolAnalytics.timestamp == latest_analytics_subquery.c.max_timestamp
                )
            ).join(
                Node,
                PoolAnalytics.node_id == Node.id
            ).filter(
                Node.last_heartbeat >= five_minutes_ago,
                Node.status == NodeStatus.ACTIVE
            ).all()
            
            if not latest_records:
                return {"avg_cpu": 0.0, "avg_memory": 0.0}
            
            # Calculate averages
            total_cpu = sum(record.avg_cpu_utilization for record in latest_records)
            total_memory = sum(record.avg_memory_utilization for record in latest_records)
            count = len(latest_records)
            
            return {
                "avg_cpu": round(total_cpu / count, 2) if count > 0 else 0.0,
                "avg_memory": round(total_memory / count, 2) if count > 0 else 0.0
            }
        except Exception as e:
            logger.error(f"Error calculating avg system metrics: {str(e)}")
            return {"avg_cpu": 0.0, "avg_memory": 0.0}
    
    @staticmethod
    def get_complete_dashboard_analytics(db: Session) -> Dict[str, Any]:
        """
        Get all dashboard metrics in a single call.
        This is the main method the API endpoint will use.
        
        Returns a dictionary matching SystemAnalyticsResponse schema.
        """
        try:
            logger.info("🔄 Calculating complete dashboard analytics...")
            
            # Calculate all metrics
            active_pools = DashboardAnalyticsCalculator.get_active_pools_24h(db)
            max_pools_today = DashboardAnalyticsCalculator.get_max_pools_today(db)
            peak_instances = DashboardAnalyticsCalculator.get_peak_instances_24h(db)
            current_instances = DashboardAnalyticsCalculator.get_current_running_instances(db)
            active_nodes = DashboardAnalyticsCalculator.get_active_nodes(db)
            avg_metrics = DashboardAnalyticsCalculator.get_avg_system_metrics(db)
            
            logger.info(f"✅ Analytics calculated: {active_pools} pools, {current_instances} instances, {active_nodes} nodes")
            
            return {
                "total_active_pools": active_pools,
                "total_current_instances": current_instances,
                "peak_instances_24h": peak_instances,
                "max_active_pools_24h": max_pools_today,
                "avg_system_cpu": avg_metrics["avg_cpu"],
                "avg_system_memory": avg_metrics["avg_memory"],
                "active_nodes": active_nodes,
                "last_updated": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"❌ Error in get_complete_dashboard_analytics: {str(e)}")
            # Return zeros on error
            return {
                "total_active_pools": 0,
                "total_current_instances": 0,
                "peak_instances_24h": 0,
                "max_active_pools_24h": 0,
                "avg_system_cpu": 0.0,
                "avg_system_memory": 0.0,
                "active_nodes": 0,
                "last_updated": datetime.utcnow()
            }
