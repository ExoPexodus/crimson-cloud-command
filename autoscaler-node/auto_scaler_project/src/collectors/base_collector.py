from abc import ABC, abstractmethod

class MetricsCollector(ABC):
    @abstractmethod
    def get_metrics(self):
        """Fetch average CPU and RAM utilization metrics."""
        pass