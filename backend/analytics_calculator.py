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
        
        Uses hourly buckets to handle asynchronous pool reporting, and ensures peak is 
        always >= current running instances.
        """
        try:
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            
            # 1. Get current running instances (ensures peak >= current)
            current_total = DashboardAnalyticsCalculator.get_current_running_instances(db)
            
            # 2. For historical data, use hourly buckets and get max per pool per hour
            hourly_subq = db.query(
                func.date_trunc('hour', PoolAnalytics.timestamp).label('hour'),
                PoolAnalytics.pool_id,
                func.max(PoolAnalytics.current_instances).label('max_instances')
            ).filter(
                PoolAnalytics.timestamp >= twenty_four_hours_ago
            ).group_by(
                func.date_trunc('hour', PoolAnalytics.timestamp),
                PoolAnalytics.pool_id
            ).subquery()
            
            # Sum all pools' max instances per hour
            hour_totals = db.query(
                hourly_subq.c.hour,
                func.sum(hourly_subq.c.max_instances).label('total')
            ).group_by(hourly_subq.c.hour).all()
            
            historical_peak = max((int(h.total) for h in hour_totals), default=0)
            
            # Peak is the maximum of current and historical
            return max(current_total, historical_peak)
        except Exception as e:
            logger.error(f"Error calculating peak instances (24h): {str(e)}")
            return 0
    
    @staticmethod
    def get_current_running_instances(db: Session) -> int:
        """
        Total instances currently running across all active pools.
        Uses fallback logic: tries 5 min, then 15 min, then 30 min windows.
        """
        try:
            # Try progressively larger time windows for more resilient data retrieval
            time_windows = [5, 15, 30]
            
            for minutes in time_windows:
                time_ago = datetime.utcnow() - timedelta(minutes=minutes)
                
                # Subquery to get the latest analytics record for each pool
                latest_analytics_subquery = db.query(
                    PoolAnalytics.pool_id,
                    func.max(PoolAnalytics.timestamp).label('max_timestamp')
                ).filter(
                    PoolAnalytics.timestamp >= time_ago
                ).group_by(
                    PoolAnalytics.pool_id
                ).subquery()
                
                # Join to get the full records and sum current_instances
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
                    Node.last_heartbeat >= time_ago,
                    Node.status == NodeStatus.ACTIVE
                ).scalar()
                
                if total and total > 0:
                    logger.debug(f"Found {total} running instances in {minutes}min window")
                    return int(total)
            
            # No data found in any window
            return 0
        except Exception as e:
            logger.error(f"Error calculating current running instances: {str(e)}")
            return 0
    
    @staticmethod
    def get_active_nodes(db: Session) -> int:
        """
        Count of nodes with recent heartbeats (within last 10 minutes) and status ACTIVE.
        Extended from 5 to 10 minutes to be more resilient to brief connectivity issues.
        """
        try:
            ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
            
            count = db.query(func.count(Node.id)).filter(
                Node.last_heartbeat >= ten_minutes_ago,
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
        Uses fallback logic: tries 5 min, then 15 min, then 30 min windows.
        """
        try:
            time_windows = [5, 15, 30]
            
            for minutes in time_windows:
                time_ago = datetime.utcnow() - timedelta(minutes=minutes)
                
                # Subquery to get the latest analytics record for each pool
                latest_analytics_subquery = db.query(
                    PoolAnalytics.pool_id,
                    func.max(PoolAnalytics.timestamp).label('max_timestamp')
                ).filter(
                    PoolAnalytics.timestamp >= time_ago
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
                    Node.last_heartbeat >= time_ago,
                    Node.status == NodeStatus.ACTIVE
                ).all()
                
                if latest_records:
                    # Calculate averages
                    total_cpu = sum(record.avg_cpu_utilization or 0 for record in latest_records)
                    total_memory = sum(record.avg_memory_utilization or 0 for record in latest_records)
                    count = len(latest_records)
                    
                    logger.debug(f"Found {count} records for avg metrics in {minutes}min window")
                    return {
                        "avg_cpu": round(total_cpu / count, 2) if count > 0 else 0.0,
                        "avg_memory": round(total_memory / count, 2) if count > 0 else 0.0
                    }
            
            # No data found in any window
            return {"avg_cpu": 0.0, "avg_memory": 0.0}
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

    @staticmethod
    def get_instance_trends(db: Session, hours: int = 24, interval: str = "hour") -> list:
        """
        Get instance count trends over time for the dashboard chart.
        Returns time-series data with total instances and avg metrics.
        
        Fix applied: Now calculates average instances PER POOL per interval first, 
        then sums those averages. This prevents over-counting when multiple logs 
        exist for the same pool in the same interval.
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            # Step 1: Calculate average metrics for each pool within each time interval
            # This collapses the 60+ logs per hour into a single representative value per pool
            subquery = db.query(
                func.date_trunc(interval, PoolAnalytics.timestamp).label('interval_ts'),
                PoolAnalytics.pool_id,
                func.avg(PoolAnalytics.current_instances).label('avg_instances'),
                func.avg(PoolAnalytics.avg_cpu_utilization).label('avg_cpu'),
                func.avg(PoolAnalytics.avg_memory_utilization).label('avg_memory')
            ).filter(
                PoolAnalytics.timestamp >= cutoff
            ).group_by(
                func.date_trunc(interval, PoolAnalytics.timestamp),
                PoolAnalytics.pool_id
            ).subquery()

            # Step 2: Sum the per-pool averages to get system-wide totals
            query = db.query(
                subquery.c.interval_ts.label('timestamp'),
                func.sum(subquery.c.avg_instances).label('total_instances'),
                func.count(distinct(subquery.c.pool_id)).label('active_pools'),
                func.avg(subquery.c.avg_cpu).label('sys_avg_cpu'),
                func.avg(subquery.c.avg_memory).label('sys_avg_memory')
            ).group_by(
                subquery.c.interval_ts
            ).order_by(
                subquery.c.interval_ts
            ).all()
            
            return [
                {
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    # Rounding to int makes sense for instances, but using round() helps with float sums
                    "total_instances": int(round(row.total_instances or 0)),
                    "active_pools": row.active_pools or 0,
                    "avg_cpu": round(row.sys_avg_cpu or 0, 2),
                    "avg_memory": round(row.sys_avg_memory or 0, 2)
                }
                for row in query
            ]
        except Exception as e:
            logger.error(f"Error getting instance trends: {str(e)}")
            return []

    @staticmethod
    def get_scaling_patterns(db: Session, hours: int = 24) -> dict:
        """
        Get scaling event patterns grouped by hour and type.
        Returns data for scaling patterns bar chart.
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            # Query scaling events from PoolAnalytics grouped by hour and type
            # We filter for rows where scaling_event is not null
            query = db.query(
                func.date_trunc('hour', PoolAnalytics.timestamp).label('timestamp'),
                PoolAnalytics.scaling_event.label('event_type'),
                func.count().label('count')
            ).filter(
                PoolAnalytics.timestamp >= cutoff,
                PoolAnalytics.scaling_event.isnot(None)
            ).group_by(
                func.date_trunc('hour', PoolAnalytics.timestamp),
                PoolAnalytics.scaling_event
            ).all()
            
            # Organize by hour
            hourly_data = {}
            for row in query:
                ts = row.timestamp.isoformat() if row.timestamp else None
                if ts not in hourly_data:
                    hourly_data[ts] = {"timestamp": ts, "scale_up": 0, "scale_down": 0, "failed": 0}
                
                event_type = (row.event_type or "").lower()
                if "up" in event_type or "out" in event_type:
                    hourly_data[ts]["scale_up"] += row.count
                elif "down" in event_type or "in" in event_type:
                    hourly_data[ts]["scale_down"] += row.count
                elif "fail" in event_type or "error" in event_type:
                    hourly_data[ts]["failed"] += row.count
            
            by_hour = sorted(hourly_data.values(), key=lambda x: x["timestamp"] or "")
            
            # Calculate totals
            totals = {
                "scale_up": sum(h["scale_up"] for h in by_hour),
                "scale_down": sum(h["scale_down"] for h in by_hour),
                "failed": sum(h["failed"] for h in by_hour),
                "other": 0
            }
            
            return {
                "by_hour": by_hour,
                "totals": totals,
                "period_hours": hours
            }
        except Exception as e:
            logger.error(f"Error getting scaling patterns: {str(e)}")
            return {"by_hour": [], "totals": {"scale_up": 0, "scale_down": 0, "failed": 0, "other": 0}, "period_hours": hours}

    @staticmethod
    def get_node_health_timeline(db: Session, node_id: int, hours: int = 24) -> dict:
        """
        Get node health timeline showing online/offline periods.
        """
        try:
            from models import NodeLifecycleLog
            
            node = db.query(Node).filter(Node.id == node_id).first()
            if not node:
                return {"error": "Node not found"}
            
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            # Get lifecycle logs for this node within the window
            logs = db.query(NodeLifecycleLog).filter(
                NodeLifecycleLog.node_id == node_id,
                NodeLifecycleLog.timestamp >= cutoff
            ).order_by(NodeLifecycleLog.timestamp).all()
            
            periods = []
            online_seconds = 0
            offline_seconds = 0
            
            # Determine initial status at the start of the window
            # If we have logs, the status BEFORE the first log is the 'previous_status' of that log
            # If no logs in window, we assume the status has been constant (match current status)
            if logs:
                initial_status = logs[0].previous_status or "offline"
                # Normalize status strings
                if initial_status.upper() in ["ACTIVE", "ONLINE"]:
                    prev_status = "online"
                else:
                    prev_status = "offline"
            else:
                # No logs in window means stable state. Use current node status.
                if node.status.value in ["ACTIVE"]:
                    prev_status = "online"
                else:
                    prev_status = "offline"

            prev_time = cutoff
            
            for log in logs:
                duration = (log.timestamp - prev_time).total_seconds()
                if prev_status == "online":
                    online_seconds += duration
                else:
                    offline_seconds += duration
                
                periods.append({
                    "status": prev_status,
                    "start": prev_time.isoformat(),
                    "end": log.timestamp.isoformat()
                })
                
                # Update status for next segment
                # Log event_type "CAME_ONLINE" -> online, "WENT_OFFLINE" -> offline
                if "ONLINE" in log.event_type.upper():
                    prev_status = "online"
                else:
                    prev_status = "offline"
                prev_time = log.timestamp
            
            # Add final period from last log (or cutoff) up to now
            now = datetime.utcnow()
            duration = (now - prev_time).total_seconds()
            if prev_status == "online":
                online_seconds += duration
            else:
                offline_seconds += duration
                
            periods.append({
                "status": prev_status,
                "start": prev_time.isoformat(),
                "end": now.isoformat()
            })
            
            total_seconds = online_seconds + offline_seconds
            uptime_percent = (online_seconds / total_seconds * 100) if total_seconds > 0 else 0
            
            return {
                "node_id": node_id,
                "node_name": node.name,
                "current_status": node.status.value if node.status else "unknown",
                "uptime_percent": round(uptime_percent, 2),
                "online_seconds": int(online_seconds),
                "offline_seconds": int(offline_seconds),
                "periods": periods,
                "last_heartbeat": node.last_heartbeat.isoformat() if node.last_heartbeat else None,
                "period_hours": hours
            }
        except Exception as e:
            logger.error(f"Error getting node health timeline: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def get_node_resource_trends(db: Session, node_id: int, hours: int = 24, interval: str = "hour") -> list:
        """
        Get CPU/Memory resource trends for a specific node.
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            # Query pool analytics for pools belonging to this node
            query = db.query(
                func.date_trunc(interval, PoolAnalytics.timestamp).label('timestamp'),
                func.avg(PoolAnalytics.avg_cpu_utilization).label('avg_cpu'),
                func.avg(PoolAnalytics.avg_memory_utilization).label('avg_memory'),
                func.max(PoolAnalytics.avg_cpu_utilization).label('max_cpu'),
                func.max(PoolAnalytics.avg_memory_utilization).label('max_memory'),
                func.sum(PoolAnalytics.current_instances).label('total_instances')
            ).join(Pool, Pool.id == PoolAnalytics.pool_id).filter(
                Pool.node_id == node_id,
                PoolAnalytics.timestamp >= cutoff
            ).group_by(
                func.date_trunc(interval, PoolAnalytics.timestamp)
            ).order_by(
                func.date_trunc(interval, PoolAnalytics.timestamp)
            ).all()
            
            return [
                {
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "avg_cpu": round(row.avg_cpu or 0, 2),
                    "avg_memory": round(row.avg_memory or 0, 2),
                    "max_cpu": round(row.max_cpu or 0, 2),
                    "max_memory": round(row.max_memory or 0, 2),
                    "total_instances": row.total_instances or 0
                }
                for row in query
            ]
        except Exception as e:
            logger.error(f"Error getting node resource trends: {str(e)}")
            return []

