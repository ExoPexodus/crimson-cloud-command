import logging
import threading
import time
from datetime import datetime
import oci
from instance_manager.instance_pool import get_instance_pool_details

class Scheduler:
    def __init__(self, compute_management_client, instance_pool_id, max_instances, schedules, scheduler_instances):
        """
        Initializes the Scheduler.

        Args:
            compute_management_client: OCI ComputeManagementClient instance.
            instance_pool_id (str): The ID of the instance pool to manage.
            max_instances (int): Maximum number of instances to add during peak time.
            schedules (list): List of schedule dictionaries with start and end times.
        """
        self.compute_management_client = compute_management_client
        self.instance_pool_id = instance_pool_id
        self.max_supported_instances = max_instances
        self.scheduler_instances = scheduler_instances
        self.schedules = schedules
        self.active_instances = 0
        self.stop_event = threading.Event()
        self.lock = threading.Lock()  # Ensure thread-safe operations
        self.currently_active = False  # Track active status
        self.scaled_up = False  # Flag to track if scaling up was done
        self.scaled_down = False  # Flag to track if scaling down was done

    def start(self):
        """Starts the scheduler in a separate thread."""
        scheduler_thread = threading.Thread(target=self.run)
        scheduler_thread.start()

    def run(self):
        """Main loop of the scheduler."""
        logging.info(f"Scheduler started for instance pool: {self.instance_pool_id}")
        while not self.stop_event.is_set():
            current_time = datetime.now().time()
            active = False

            for schedule in self.schedules:
                start_time = datetime.strptime(schedule['start_time'], '%H:%M').time()
                end_time = datetime.strptime(schedule['end_time'], '%H:%M').time()

                if start_time <= current_time <= end_time:
                    active = True
                    self.currently_active = active  # Update the active status
                    self.execute_schedule_logic(current_time, start_time, end_time)
                    break  # Exit loop once the active schedule is found

            if not active:
                self.currently_active = active
                logging.info(f"Scheduler is currently inactive for pool {self.instance_pool_id}. Resetting scale flags.")
                self.scaled_up = False  # Reset the flag when schedule period is over
                self.scaled_down = False  # Reset the flag when schedule period is over
                time.sleep(60)  # Sleep for 1 minute before checking again

    def is_active(self):
        """Returns whether the scheduler is currently active."""
        return self.currently_active

    def execute_schedule_logic(self, current_time, start_time, end_time):
        """Executes the add/remove logic during the active schedule period."""
        logging.info(f"Scheduler is active between {start_time} and {end_time} for pool {self.instance_pool_id}")

        pool_details = get_instance_pool_details(self.compute_management_client, self.instance_pool_id)
        current_size = pool_details.size

        # Scale up only once per active schedule window
        if not self.scaled_up and current_size < self.max_supported_instances:
            self.add_instances(self.scheduler_instances)
            self.scaled_up = True  # Mark that scaling up was done

        # Scale down only once after the schedule window ends
        if current_time > end_time and not self.scaled_down and current_size > self.scheduler_instances:
            self.remove_instances(self.scheduler_instances)
            self.scaled_down = True  # Mark that scaling down was done
        
        time.sleep(60)

    def add_instances(self, count):
        """Adds instances to the instance pool using OCI SDK."""
        with self.lock:
            pool_details = get_instance_pool_details(self.compute_management_client, self.instance_pool_id)
            current_size = pool_details.size
            new_size = current_size + count

            if new_size > self.max_supported_instances:
                logging.warning(f"Cannot add {count} instances; max limit reached.")
                return

            try:
                logging.info(f"Adding {count} instances to pool {self.instance_pool_id}.")
                self.compute_management_client.update_instance_pool(
                    instance_pool_id=self.instance_pool_id,
                    update_instance_pool_details=oci.core.models.UpdateInstancePoolDetails(size=new_size),
                )
                self.active_instances += count
                logging.info(f"{count} instances added. New size: {new_size}")
            except Exception as e:
                logging.error(f"Error adding instances: {e}")

    def remove_instances(self, count):
        """Removes instances from the instance pool using OCI SDK."""
        with self.lock:
            pool_details = get_instance_pool_details(self.compute_management_client, self.instance_pool_id)
            current_size = pool_details.size
            new_size = current_size - count

            if new_size < 0:
                logging.warning(f"Cannot remove {count} instances; pool size would be negative.")
                return

            try:
                logging.info(f"Removing {count} instances from pool {self.instance_pool_id}.")
                self.compute_management_client.update_instance_pool(
                    instance_pool_id=self.instance_pool_id,
                    update_instance_pool_details=oci.core.models.UpdateInstancePoolDetails(size=new_size),
                )
                self.active_instances -= count
                logging.info(f"{count} instances removed. New size: {new_size}")
            except Exception as e:
                logging.error(f"Error removing instances: {e}")

    def stop(self):
        """Stops the scheduler."""
        logging.info(f"Stopping scheduler for instance pool: {self.instance_pool_id}")
        self.stop_event.set()
