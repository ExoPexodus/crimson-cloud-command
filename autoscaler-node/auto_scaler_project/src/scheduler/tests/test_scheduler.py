
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, time
import threading
import time as time_module
from scheduler.scheduler import Scheduler
from scheduler.utils.time_utils import is_time_in_range, parse_cron_expression

class TestScheduler(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_compute_client = Mock()
        self.mock_pool_details = Mock()
        self.mock_pool_details.size = 2
        self.mock_compute_client.get_instance_pool.return_value.data = self.mock_pool_details
        
        self.instance_pool_id = "test-pool-123"
        self.max_instances = 10
        self.scheduler_instances = 5
        
        # Test schedule - active between 09:00 and 17:00
        self.schedules = [
            {
                'start_time': '09:00',
                'end_time': '17:00',
                'name': 'business_hours'
            }
        ]
        
        self.scheduler = Scheduler(
            compute_management_client=self.mock_compute_client,
            instance_pool_id=self.instance_pool_id,
            max_instances=self.max_instances,
            schedules=self.schedules,
            scheduler_instances=self.scheduler_instances
        )

    def test_scheduler_initialization(self):
        """Test scheduler initializes correctly."""
        self.assertEqual(self.scheduler.instance_pool_id, self.instance_pool_id)
        self.assertEqual(self.scheduler.max_supported_instances, self.max_instances)
        self.assertEqual(self.scheduler.scheduler_instances, self.scheduler_instances)
        self.assertEqual(self.scheduler.schedules, self.schedules)
        self.assertFalse(self.scheduler.currently_active)
        self.assertFalse(self.scheduler.scaled_up)
        self.assertFalse(self.scheduler.scaled_down)

    def test_is_active_initially_false(self):
        """Test scheduler is initially inactive."""
        self.assertFalse(self.scheduler.is_active())

    @patch('scheduler.scheduler.get_instance_pool_details')
    def test_add_instances(self, mock_get_details):
        """Test adding instances to the pool."""
        mock_get_details.return_value = self.mock_pool_details
        
        self.scheduler.add_instances(3)
        
        # Verify the update_instance_pool was called with correct new size
        self.mock_compute_client.update_instance_pool.assert_called_once()
        call_args = self.mock_compute_client.update_instance_pool.call_args
        self.assertEqual(call_args[1]['instance_pool_id'], self.instance_pool_id)
        # New size should be current (2) + added (3) = 5
        update_details = call_args[1]['update_instance_pool_details']
        self.assertEqual(update_details.size, 5)

    @patch('scheduler.scheduler.get_instance_pool_details')
    def test_remove_instances(self, mock_get_details):
        """Test removing instances from the pool."""
        mock_get_details.return_value = self.mock_pool_details
        
        self.scheduler.remove_instances(1)
        
        # Verify the update_instance_pool was called with correct new size
        self.mock_compute_client.update_instance_pool.assert_called_once()
        call_args = self.mock_compute_client.update_instance_pool.call_args
        self.assertEqual(call_args[1]['instance_pool_id'], self.instance_pool_id)
        # New size should be current (2) - removed (1) = 1
        update_details = call_args[1]['update_instance_pool_details']
        self.assertEqual(update_details.size, 1)

    def test_add_instances_exceeds_max(self):
        """Test adding instances doesn't exceed maximum limit."""
        # Set current size to max - 1
        self.mock_pool_details.size = self.max_instances - 1
        
        with patch('scheduler.scheduler.get_instance_pool_details', return_value=self.mock_pool_details):
            self.scheduler.add_instances(5)  # Try to add more than allowed
        
        # Should not call update since it would exceed max
        self.mock_compute_client.update_instance_pool.assert_not_called()

    def test_remove_instances_below_zero(self):
        """Test removing instances doesn't go below zero."""
        # Set current size to 1
        self.mock_pool_details.size = 1
        
        with patch('scheduler.scheduler.get_instance_pool_details', return_value=self.mock_pool_details):
            self.scheduler.remove_instances(5)  # Try to remove more than available
        
        # Should not call update since it would go negative
        self.mock_compute_client.update_instance_pool.assert_not_called()

    def test_stop_scheduler(self):
        """Test stopping the scheduler sets the stop event."""
        self.scheduler.stop()
        self.assertTrue(self.scheduler.stop_event.is_set())

    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.scheduler, 'stop_event'):
            self.scheduler.stop()


class TestTimeUtils(unittest.TestCase):
    def test_is_time_in_range_normal(self):
        """Test time range checking for normal ranges (not overnight)."""
        # Test time within range
        test_time = datetime.strptime('10:30', '%H:%M')
        self.assertTrue(is_time_in_range('09:00', '17:00', test_time))
        
        # Test time outside range
        test_time = datetime.strptime('18:30', '%H:%M')
        self.assertFalse(is_time_in_range('09:00', '17:00', test_time))
        
        # Test time at boundaries
        test_time = datetime.strptime('09:00', '%H:%M')
        self.assertTrue(is_time_in_range('09:00', '17:00', test_time))
        
        test_time = datetime.strptime('17:00', '%H:%M')
        self.assertTrue(is_time_in_range('09:00', '17:00', test_time))

    def test_is_time_in_range_overnight(self):
        """Test time range checking for overnight ranges."""
        # Test time within overnight range
        test_time = datetime.strptime('23:30', '%H:%M')
        self.assertTrue(is_time_in_range('22:00', '06:00', test_time))
        
        test_time = datetime.strptime('03:30', '%H:%M')
        self.assertTrue(is_time_in_range('22:00', '06:00', test_time))
        
        # Test time outside overnight range
        test_time = datetime.strptime('12:30', '%H:%M')
        self.assertFalse(is_time_in_range('22:00', '06:00', test_time))

    def test_parse_cron_expression(self):
        """Test parsing cron expressions."""
        cron = "0 9 * * *"
        result = parse_cron_expression(cron)
        
        expected = {
            'minute': '0',
            'hour': '9',
            'day': '*',
            'month': '*',
            'day_of_week': '*'
        }
        
        self.assertEqual(result, expected)

    def test_parse_cron_expression_invalid(self):
        """Test parsing invalid cron expressions."""
        with self.assertRaises(ValueError):
            parse_cron_expression("0 9 *")  # Too few parts
        
        with self.assertRaises(ValueError):
            parse_cron_expression("0 9 * * * *")  # Too many parts


if __name__ == '__main__':
    unittest.main()
