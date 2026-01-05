# Workflow Engine Design

## 1. Overview

The autoscaling workflow engine is the core decision-making component that evaluates metrics and determines when to scale instance pools. It operates as a continuous loop on each autoscaler node, independent of the central management system.

---

## 2. Core Workflow Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AUTOSCALER MAIN LOOP                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│     START       │
│  (main.py)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Load config.yaml│
│ Initialize OCI  │
│ clients         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Auto-register   │
│ with backend    │
│ (if needed)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Sync config with│
│ central backend │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Start heartbeat │
│ thread (60s)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ For each pool   │────►│ process_pool()  │
│ in config       │     │ (new thread)    │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ POOL MONITORING │
                        │     LOOP        │◄───────────────────┐
                        └────────┬────────┘                    │
                                 │                             │
                                 ▼                             │
                        ┌─────────────────┐                    │
                        │ Collect metrics │                    │
                        │ (OCI/Prometheus)│                    │
                        └────────┬────────┘                    │
                                 │                             │
                                 ▼                             │
                        ┌─────────────────┐                    │
                        │ Evaluate scaling│                    │
                        │ thresholds      │                    │
                        └────────┬────────┘                    │
                                 │                             │
                       ┌─────────┴─────────┐                   │
                       │                   │                   │
                       ▼                   ▼                   │
              ┌─────────────┐     ┌─────────────┐              │
              │ Scale UP    │     │ Scale DOWN  │              │
              │ (if needed) │     │ (if needed) │              │
              └─────────────┘     └─────────────┘              │
                       │                   │                   │
                       └─────────┬─────────┘                   │
                                 │                             │
                                 ▼                             │
                        ┌─────────────────┐                    │
                        │ Report analytics│                    │
                        │ to backend      │                    │
                        └────────┬────────┘                    │
                                 │                             │
                                 ▼                             │
                        ┌─────────────────┐                    │
                        │ Sleep 5 minutes │────────────────────┘
                        └─────────────────┘
```

---

## 3. Metrics Collection Workflow

### 3.1 Collector Selection

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        METRICS COLLECTOR FACTORY                             │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │ get_collector() │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Read monitoring │
                    │ method from     │
                    │ pool config     │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │ method =      │ │ method =      │ │ method =      │
    │ "oci"         │ │ "prometheus"  │ │ unknown       │
    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │                 │                 │
            ▼                 ▼                 ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │ Return        │ │ Return        │ │ Raise         │
    │ OCIMetrics    │ │ PrometheusMetrics│ │ ValueError │
    │ Collector     │ │ Collector     │ │               │
    └───────────────┘ └───────────────┘ └───────────────┘
```

### 3.2 OCI Metrics Collection

```python
# OCI Collector Flow

class OCIMetricsCollector:
    def get_metrics(self):
        """
        1. Get all instances in the pool
        2. For each instance, fetch CPU and memory metrics
        3. Calculate averages across all instances
        4. Return (avg_cpu, avg_ram)
        """
        
        # Step 1: Get instances from pool
        instances = get_instances_from_instance_pool(
            client=self.compute_management_client,
            pool_id=self.instance_pool_id,
            compartment_id=self.compartment_id
        )
        
        # Step 2: Fetch metrics for each instance
        all_cpu_values = []
        all_ram_values = []
        
        for instance in instances:
            cpu, ram = self.fetch_instance_metrics(instance.id)
            all_cpu_values.append(cpu)
            all_ram_values.append(ram)
        
        # Step 3: Calculate averages
        avg_cpu = sum(all_cpu_values) / len(all_cpu_values)
        avg_ram = sum(all_ram_values) / len(all_ram_values)
        
        return avg_cpu, avg_ram
```

### 3.3 Prometheus Metrics Collection

```python
# Prometheus Collector Flow

class PrometheusMetricsCollector:
    def get_metrics(self):
        """
        1. Get all instances in the pool
        2. Query Prometheus for each instance hostname
        3. Calculate averages across all instances
        4. Return (avg_cpu, avg_ram)
        """
        
        # Step 1: Get instances
        instances = get_instances_from_instance_pool(...)
        
        # Step 2: Query Prometheus
        all_metrics = []
        for instance in instances:
            hostname = instance.hostname
            cpu, ram = get_cpu_ram_metrics(hostname, self.prometheus_url)
            all_metrics.append((cpu, ram))
        
        # Step 3: Calculate averages
        avg_cpu = sum(m[0] for m in all_metrics) / len(all_metrics)
        avg_ram = sum(m[1] for m in all_metrics) / len(all_metrics)
        
        return avg_cpu, avg_ram
```

---

## 4. Scaling Decision Engine

### 4.1 Evaluation Algorithm

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SCALING DECISION FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │ evaluate_metrics│
                    │ (collector,     │
                    │  thresholds,    │
                    │  limits)        │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Get current     │
                    │ avg_cpu, avg_ram│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Get current     │
                    │ instance count  │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │ avg_cpu >     │ │ avg_cpu <     │ │ Thresholds    │
    │ cpu_threshold │ │ lower_bound   │ │ within range  │
    │ OR            │ │ AND           │ │               │
    │ avg_ram >     │ │ avg_ram <     │ │               │
    │ ram_threshold │ │ lower_bound   │ │               │
    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │                 │                 │
            ▼                 ▼                 ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │ Check if      │ │ Check if      │ │ No action     │
    │ current <     │ │ current >     │ │ needed        │
    │ max_instances │ │ min_instances │ │               │
    └───────┬───────┘ └───────┬───────┘ └───────────────┘
            │                 │
            ▼                 ▼
    ┌───────────────┐ ┌───────────────┐
    │ Check if      │ │ Check if      │
    │ scheduler is  │ │ scheduler is  │
    │ NOT active    │ │ NOT active    │
    └───────┬───────┘ └───────┬───────┘
            │                 │
            ▼                 ▼
    ┌───────────────┐ ┌───────────────┐
    │ SCALE UP      │ │ SCALE DOWN    │
    │ Add 1 instance│ │ Remove 1 inst │
    └───────────────┘ └───────────────┘
```

### 4.2 Threshold Configuration

```yaml
# config.yaml example

pools:
  - instance_pool_id: "ocid1.instancepool.oc1..."
    region: "us-ashburn-1"
    monitoring_method: "oci"
    
    # Thresholds for scaling decisions
    cpu_threshold: 80          # Scale up if CPU > 80%
    ram_threshold: 80          # Scale up if RAM > 80%
    
    # Scaling limits
    scaling_limits:
      min: 2                   # Never go below 2 instances
      max: 10                  # Never exceed 10 instances
    
    # Optional: scheduled scaling
    schedules:
      - name: "business_hours"
        start_time: "08:00"
        end_time: "18:00"
        target_instances: 5
```

### 4.3 Scaling Logic Code

```python
def evaluate_metrics(collector, thresholds, scaling_limits, scheduler_active_callback):
    """
    Core scaling decision function.
    
    Args:
        collector: MetricsCollector instance
        thresholds: Dict with cpu and ram threshold percentages
        scaling_limits: Dict with min and max instance counts
        scheduler_active_callback: Function returning True if scheduler is active
    """
    
    # Get current metrics
    try:
        avg_cpu, avg_ram = collector.get_metrics()
    except Exception as e:
        logging.error(f"Failed to get metrics: {e}")
        return
    
    # Validate metrics
    if avg_cpu is None or avg_ram is None:
        logging.warning("Invalid metrics received, skipping evaluation")
        return
    
    # Get current instance count
    pool_details = collector.compute_management_client.get_instance_pool(
        instance_pool_id=collector.instance_pool_id
    ).data
    current_size = pool_details.size
    
    # Check if scheduler is active (prevents auto-scaling during scheduled periods)
    if scheduler_active_callback():
        logging.info("Scheduler is active, skipping auto-scaling evaluation")
        return
    
    # Scaling decision
    min_instances = scaling_limits["min"]
    max_instances = scaling_limits["max"]
    cpu_threshold = thresholds["cpu"]
    ram_threshold = thresholds["ram"]
    
    # Scale UP condition
    if (avg_cpu > cpu_threshold or avg_ram > ram_threshold):
        if current_size < max_instances:
            logging.info(f"Scaling UP: CPU={avg_cpu}%, RAM={avg_ram}%")
            scale_up(collector, current_size + 1)
        else:
            logging.info(f"At max instances ({max_instances}), cannot scale up")
    
    # Scale DOWN condition (using 50% of threshold as lower bound)
    elif (avg_cpu < cpu_threshold * 0.5 and avg_ram < ram_threshold * 0.5):
        if current_size > min_instances:
            logging.info(f"Scaling DOWN: CPU={avg_cpu}%, RAM={avg_ram}%")
            scale_down(collector, current_size - 1)
        else:
            logging.info(f"At min instances ({min_instances}), cannot scale down")
    
    else:
        logging.debug(f"No scaling needed: CPU={avg_cpu}%, RAM={avg_ram}%")
```

---

## 5. Scheduler Workflow

### 5.1 Schedule Evaluation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SCHEDULER WORKFLOW                                    │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │ Scheduler.run() │
                    │ (loop every 60s)│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Get current time│
                    │ (local timezone)│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ For each        │
                    │ schedule in     │
                    │ config          │
                    └────────┬────────┘
                             │
            ┌────────────────┴────────────────┐
            │                                 │
            ▼                                 ▼
    ┌───────────────────┐           ┌───────────────────┐
    │ Is current time   │           │ Is current time   │
    │ WITHIN schedule?  │           │ OUTSIDE schedule? │
    │ (start <= now     │           │                   │
    │  <= end)          │           │                   │
    └─────────┬─────────┘           └─────────┬─────────┘
              │                               │
              ▼                               ▼
    ┌───────────────────┐           ┌───────────────────┐
    │ Set scheduler     │           │ Set scheduler     │
    │ ACTIVE = True     │           │ ACTIVE = False    │
    └─────────┬─────────┘           └───────────────────┘
              │
              ▼
    ┌───────────────────┐
    │ Get current       │
    │ instance count    │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────────┐   ┌─────────────┐
│ current <   │   │ current >   │
│ target      │   │ target      │
└──────┬──────┘   └──────┬──────┘
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│ ADD         │   │ REMOVE      │
│ instances   │   │ instances   │
│ to reach    │   │ to reach    │
│ target      │   │ target      │
└─────────────┘   └─────────────┘
```

### 5.2 Schedule Priority

The scheduler takes precedence over metric-based autoscaling:

1. When a schedule is **active**, the `scheduler_active_callback()` returns `True`
2. The `evaluate_metrics()` function checks this callback and skips scaling if active
3. The scheduler manages instance count directly to the target value
4. When the schedule ends, normal autoscaling resumes

---

## 6. Heartbeat Workflow

### 6.1 Heartbeat Service Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        HEARTBEAT WORKFLOW                                    │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │ HeartbeatService│
                    │ .start()        │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Every 60 seconds│◄─────────────────────────┐
                    └────────┬────────┘                          │
                             │                                   │
                             ▼                                   │
                    ┌─────────────────┐                          │
                    │ Collect pool    │                          │
                    │ analytics data  │                          │
                    └────────┬────────┘                          │
                             │                                   │
                             ▼                                   │
                    ┌─────────────────┐                          │
                    │ POST /heartbeat │                          │
                    │ to backend      │                          │
                    │ - status        │                          │
                    │ - config_hash   │                          │
                    │ - pool_analytics│                          │
                    └────────┬────────┘                          │
                             │                                   │
                             ▼                                   │
                    ┌─────────────────┐                          │
                    │ Check response  │                          │
                    └────────┬────────┘                          │
                             │                                   │
            ┌────────────────┼────────────────┐                  │
            │                │                │                  │
            ▼                ▼                ▼                  │
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐        │
    │ config_update │ │ Normal        │ │ Error         │        │
    │ _needed: true │ │ response      │ │ response      │        │
    └───────┬───────┘ └───────────────┘ └───────┬───────┘        │
            │                                   │                │
            ▼                                   ▼                │
    ┌───────────────┐                   ┌───────────────┐        │
    │ GET /nodes/   │                   │ Log error,    │        │
    │ {id}/config   │                   │ continue      │        │
    └───────┬───────┘                   └───────────────┘        │
            │                                                    │
            ▼                                                    │
    ┌───────────────┐                                            │
    │ Update local  │                                            │
    │ config.yaml   │                                            │
    └───────┬───────┘                                            │
            │                                                    │
            ▼                                                    │
    ┌───────────────┐                                            │
    │ Restart pool  │                                            │
    │ monitoring    │                                            │
    │ threads       │                                            │
    └───────────────┘                                            │
            │                                                    │
            └────────────────────────────────────────────────────┘
```

---

## 7. Configuration Sync Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONFIGURATION SYNC FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │ User edits      │
                    │ config in UI    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ PUT /nodes/{id} │
                    │ /config         │
                    │ { yaml_config } │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Backend saves   │
                    │ new config with │
                    │ new hash        │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ On next node    │
                    │ heartbeat...    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Backend compares│
                    │ node's hash vs  │
                    │ stored hash     │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐
    │ Hashes match  │ │ Hashes differ │
    └───────────────┘ └───────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Return response │
                    │ config_update   │
                    │ _needed: true   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Node fetches    │
                    │ new config and  │
                    │ restarts pools  │
                    └─────────────────┘
```

---

## 8. Error Handling

### 8.1 Metrics Collection Errors

```python
# Error handling in metrics collection

def get_metrics(self):
    try:
        instances = get_instances_from_instance_pool(...)
    except ServiceError as e:
        if e.status == 404:
            logging.error("Instance pool not found")
            raise RuntimeError("Pool configuration invalid")
        elif e.status == 401:
            logging.error("OCI authentication failed")
            raise RuntimeError("OCI credentials invalid")
        else:
            logging.error(f"OCI API error: {e}")
            raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise RuntimeError(f"Metrics collection failed: {e}")
```

### 8.2 Scaling Operation Errors

```python
# Retry logic for scaling operations

def scale_up(collector, target_size, max_retries=3):
    for attempt in range(max_retries):
        try:
            collector.compute_management_client.update_instance_pool(
                instance_pool_id=collector.instance_pool_id,
                update_instance_pool_details={
                    "size": target_size
                }
            )
            logging.info(f"Successfully scaled to {target_size} instances")
            return True
        except ServiceError as e:
            if e.status in [429, 500, 503]:  # Retryable errors
                wait_time = 2 ** attempt  # Exponential backoff
                logging.warning(f"Scaling failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logging.error(f"Scaling failed with non-retryable error: {e}")
                return False
    
    logging.error(f"Scaling failed after {max_retries} attempts")
    return False
```

### 8.3 Backend Communication Errors

```python
# Heartbeat service error handling

def send_heartbeat(self, status, pool_analytics, config_hash):
    try:
        response = requests.post(
            f"{self.backend_url}/heartbeat",
            headers={"X-API-Key": self.api_key},
            json={
                "node_id": self.node_id,
                "status": status,
                "pool_analytics": pool_analytics,
                "config_hash": config_hash
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        logging.warning("Heartbeat request timed out")
        return None
    except requests.ConnectionError:
        logging.warning("Cannot connect to backend")
        return None
    except Exception as e:
        logging.error(f"Heartbeat failed: {e}")
        return None
```
