from prometheus_api_client import PrometheusConnect


def get_cpu_ram_metrics(instance_hostname, prometheus_url):
    prom = PrometheusConnect(url=prometheus_url, disable_ssl=True)

    # CPU utilization query for the specific instance
    cpu_query = f'100 - (avg by (instance) (rate(node_cpu_seconds_total{{mode="idle", instance="{instance_hostname}"}}[5m])) * 100)'
    
    # RAM utilization query for the specific instance
    ram_query = f'(node_memory_Active_bytes{{instance="{instance_hostname}"}} / node_memory_MemTotal_bytes{{instance="{instance_hostname}"}}) * 100'
    
    cpu_data = prom.custom_query(query=cpu_query)
    ram_data = prom.custom_query(query=ram_query)
    
    return cpu_data, ram_data