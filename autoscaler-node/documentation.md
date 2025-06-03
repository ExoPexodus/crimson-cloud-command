# OCI and Prometheus Metrics Collector Codebase Documentation

This codebase provides a modular framework for collecting CPU and RAM utilization metrics from instances managed through Oracle Cloud Infrastructure (OCI) or Prometheus. It defines a base class, `MetricsCollector`, with two specific implementations:
- **`OCIMetricsCollector`**: Fetches metrics using OCI's MonitoringClient.
- **`PrometheusMetricsCollector`**: Fetches metrics from a Prometheus server.

The framework also includes utility functions for managing OCI instance pools and a centralized logging mechanism.

---

## **File Structure**

1. **`main.py`**: Entry point for the application, orchestrates metric collection.
2. **`oci_collector.py`**: Implementation of the `OCIMetricsCollector` class.
3. **`prometheus_collector.py`**: Implementation of the `PrometheusMetricsCollector` class.
4. **`base_collector.py`**: Defines the abstract base class `MetricsCollector`.
5. **`instance_manager/`**: Utilities for managing OCI instance pools.
6. **`prometheus_metrics/`**: Functions to query Prometheus for CPU and RAM metrics.

---

## **Key Components**

### 1. **Base Collector**
File: `collectors/base_collector.py`

#### Description:
The `MetricsCollector` abstract base class provides a template for implementing specific metric collectors.

#### Abstract Methods:
- **`get_metrics()`**: Fetches average CPU and RAM utilization across instances.

---

### 2. **OCI Metrics Collector**
File: `oci_collector.py`

#### Description:
Fetches metrics using OCI’s MonitoringClient. Metrics include:
- **CPU Utilization**
- **Memory Utilization**

#### Class: `OCIMetricsCollector`
**Constructor Parameters**:
- `monitoring_client`: Instance of `oci.monitoring.MonitoringClient`.
- `compute_management_client`: Instance of `oci.core.ComputeManagementClient`.
- `instance_manager`: Manager for fetching instances from a pool.
- `instance_pool_id`: OCID of the instance pool.
- `compartment_id`: OCID of the compartment.

**Key Methods**:
1. **`fetch_instance_metrics(instance_id)`**:
   - Fetches CPU and memory metrics for a single instance.
   - **Inputs**: Instance OCID.
   - **Returns**: `(cpu_utilization, memory_utilization)` tuple.

2. **`get_metrics()`**:
   - Fetches average metrics across all instances in a pool.
   - **Raises**: `RuntimeError` if instances are missing or metrics cannot be fetched.

---

### 3. **Prometheus Metrics Collector**
File: `prometheus_collector.py`

#### Description:
Fetches metrics from Prometheus using instance hostnames.

#### Class: `PrometheusMetricsCollector`
**Constructor Parameters**:
- `prometheus_url`: URL of the Prometheus server.
- `compute_management_client`: Instance of `oci.core.ComputeManagementClient`.
- `instance_pool_id`: OCID of the instance pool.
- `compartment_id`: OCID of the compartment.

**Key Methods**:
1. **`get_metrics()`**:
   - Fetches average CPU and memory utilization across instances.
   - Queries Prometheus using `get_cpu_ram_metrics()` for each instance.

---

### 4. **Instance Manager**
Directory: `instance_manager/`

#### Description:
Contains utility functions for managing and querying OCI instance pools.

**Key Function**:
- **`get_instances_from_instance_pool(client, pool_id, compartment_id)`**:
  - Fetches a list of instances in the specified instance pool.

---

### 5. **Prometheus Metrics Client**
Directory: `prometheus_metrics/`

#### Description:
Provides helper functions to fetch metrics from Prometheus.

**Key Function**:
- **`get_cpu_ram_metrics(instance_hostname, prometheus_url)`**:
  - Fetches CPU and RAM utilization data for a given instance from Prometheus.
  - **Inputs**: Instance hostname, Prometheus server URL.
  - **Returns**: `(cpu_data, ram_data)`.

---

### 6. **Main Application**
File: `main.py`

#### Description:
The entry point for orchestrating metric collection from various sources.

#### Key Functions:
1. **`get_collector(pool, compute_management_client, monitoring_client)`**:
   - Returns a `MetricsCollector` instance based on the configuration.
   - Supports both OCI and Prometheus collectors.

2. **`process_pool(pool)`**:
   - Fetches metrics for a given pool using the appropriate collector.

3. **`main()`**:
   - Initializes clients and processes all configured pools.

---

## **Error Handling**

### OCI Collector
- Logs errors at the instance level and continues collecting metrics for other instances.
- Raises `RuntimeError` for critical failures, halting execution.

### Prometheus Collector
- Logs errors if metrics cannot be fetched for specific instances.
- Raises `RuntimeError` for critical issues (e.g., no instances found).

### General
- Centralized logging ensures all errors and important events are logged for debugging.

---

## **Logging**

Logging is enabled throughout the application to provide detailed insights:
- **`debug`**: For detailed step-by-step execution.
- **`info`**: For summary metrics and successful operations.
- **`error`**: For issues encountered during metric collection.

---

## **Extensibility**

This framework is designed to be extensible:
1. **Adding a New Metrics Source**:
   - Implement a new subclass of `MetricsCollector`.
   - Provide implementations for all abstract methods.
   - Update `get_collector()` in `main.py` to include the new source.

2. **Modifying Metric Logic**:
   - Update the `fetch_instance_metrics()` method for OCI.
   - Update the `get_cpu_ram_metrics()` function for Prometheus.

---

## **Future Improvements**

1. **Graceful Failure Handling**:
   - Add retry logic for transient failures (e.g., network issues).
   - Implement circuit breakers for failed services.

2. **Asynchronous Execution**:
   - Use asyncio for non-blocking metric collection.

3. **Centralized Configuration**:
   - Move all parameters (e.g., OCIDs, URLs) to a centralized YAML or JSON configuration file.

4. **Containerization**:
   - Ensure compatibility with Docker for easy deployment.

5. **Monitoring**:
   - Add health checks and observability features for the collectors themselves.

---

## **Usage Example**

### Running the Application
1. Set up your environment with necessary OCI credentials and Prometheus URLs.
2. Run the application:
   ```bash
   python main.py
   ```
3. Check logs for outputs and errors.

---