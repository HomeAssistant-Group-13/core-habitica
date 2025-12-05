"""Test the Habitica user coordinator."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, PropertyMock, patch

from freezegun.api import FrozenDateTimeFactory
from habiticalib import TaskData
import pytest

from homeassistant.components.habitica.const import UNSCORED_TASK_ALERT_HOURS
from homeassistant.components.habitica.coordinators.user import (
    HabiticaDataUpdateCoordinator,
)
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, async_capture_events


@pytest.mark.usefixtures("habitica")
async def test_check_unscored_tasks_with_completed_task(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test _check_unscored_tasks skips completed tasks."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator: HabiticaDataUpdateCoordinator = config_entry.runtime_data

    # Create a completed task that's old enough to trigger alert
    old_timestamp = datetime.now(UTC) - timedelta(hours=UNSCORED_TASK_ALERT_HOURS + 1)
    mock_task = MagicMock(spec=TaskData)
    mock_task.id = "test-task-id"
    mock_task.text = "Test completed task"
    mock_task.Type = MagicMock(value="todo")
    mock_task.updatedAt = old_timestamp
    mock_task.completed = True  # This should cause the task to be skipped

    events = async_capture_events(hass, "habitica_unscored_task_alert")

    await coordinator._check_unscored_tasks([mock_task])

    # Should NOT fire event because task is completed
    assert len(events) == 0


@pytest.mark.usefixtures("habitica")
async def test_check_unscored_tasks_without_updated_at(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test _check_unscored_tasks skips tasks without updatedAt attribute."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator: HabiticaDataUpdateCoordinator = config_entry.runtime_data

    # Create a task without updatedAt attribute
    mock_task = MagicMock(spec=TaskData)
    mock_task.id = "test-task-id"
    mock_task.text = "Test task without timestamp"
    mock_task.Type = MagicMock(value="todo")
    mock_task.completed = False
    # Simulate missing updatedAt attribute
    type(mock_task).updatedAt = PropertyMock(side_effect=AttributeError)

    events = async_capture_events(hass, "habitica_unscored_task_alert")

    await coordinator._check_unscored_tasks([mock_task])

    # Should NOT fire event because task has no updatedAt
    assert len(events) == 0


@pytest.mark.usefixtures("habitica")
async def test_check_unscored_tasks_with_none_updated_at(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test _check_unscored_tasks skips tasks with None updatedAt."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator: HabiticaDataUpdateCoordinator = config_entry.runtime_data

    # Create a task with None updatedAt
    mock_task = MagicMock(spec=TaskData)
    mock_task.id = "test-task-id"
    mock_task.text = "Test task with None timestamp"
    mock_task.Type = MagicMock(value="todo")
    mock_task.completed = False
    mock_task.updatedAt = None

    events = async_capture_events(hass, "habitica_unscored_task_alert")

    await coordinator._check_unscored_tasks([mock_task])

    # Should NOT fire event because updatedAt is None
    assert len(events) == 0


@pytest.mark.usefixtures("habitica")
async def test_check_unscored_tasks_exception_handling_attribute_error(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test _check_unscored_tasks handles AttributeError gracefully."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator: HabiticaDataUpdateCoordinator = config_entry.runtime_data

    # Create a task that will raise AttributeError when accessing updatedAt.tzinfo
    mock_task = MagicMock(spec=TaskData)
    mock_task.id = "test-task-id"
    mock_task.text = "Test task with error"
    mock_task.Type = MagicMock(value="todo")
    mock_task.completed = False
    # Mock updatedAt to have a tzinfo property that raises AttributeError
    mock_dt = MagicMock()
    type(mock_dt).tzinfo = PropertyMock(side_effect=AttributeError("test error"))
    mock_task.updatedAt = mock_dt

    events = async_capture_events(hass, "habitica_unscored_task_alert")

    await coordinator._check_unscored_tasks([mock_task])

    # Should NOT fire event and should log debug message
    assert len(events) == 0
    assert "Error checking task" in caplog.text
    assert "Test task with error" in caplog.text


@pytest.mark.usefixtures("habitica")
async def test_check_unscored_tasks_exception_handling_type_error(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test _check_unscored_tasks handles TypeError gracefully."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator: HabiticaDataUpdateCoordinator = config_entry.runtime_data

    # Create a task with invalid timestamp that causes TypeError
    mock_task = MagicMock(spec=TaskData)
    mock_task.id = "test-task-id"
    mock_task.text = "Test task with type error"
    mock_task.Type = MagicMock(value="todo")
    mock_task.completed = False
    mock_task.updatedAt = "not-a-datetime"  # Invalid type

    events = async_capture_events(hass, "habitica_unscored_task_alert")

    await coordinator._check_unscored_tasks([mock_task])

    # Should NOT fire event and should log debug message
    assert len(events) == 0
    assert "Error checking task" in caplog.text


@pytest.mark.usefixtures("habitica")
async def test_check_unscored_tasks_exception_handling_value_error(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test _check_unscored_tasks handles ValueError gracefully."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator: HabiticaDataUpdateCoordinator = config_entry.runtime_data

    # Create a task that will cause ValueError during time calculation
    mock_task = MagicMock(spec=TaskData)
    mock_task.id = "test-task-id"
    mock_task.text = "Test task with value error"
    mock_task.Type = MagicMock(value="todo")
    mock_task.completed = False
    # Make the subtraction raise ValueError
    mock_updated_at = MagicMock()
    mock_updated_at.tzinfo = None
    mock_updated_at.replace.return_value.__sub__.side_effect = ValueError("Invalid")
    mock_task.updatedAt = mock_updated_at

    events = async_capture_events(hass, "habitica_unscored_task_alert")

    await coordinator._check_unscored_tasks([mock_task])

    # Should NOT fire event and should log debug message
    assert len(events) == 0
    assert "Error checking task" in caplog.text


@pytest.mark.usefixtures("habitica")
async def test_adjust_polling_for_activity_low_activity_branch(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test _adjust_polling_for_activity with low activity (1+ hour ago)."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator: HabiticaDataUpdateCoordinator = config_entry.runtime_data

    # Set last activity time to more than 1 hour ago
    base_time = datetime.now(UTC)
    coordinator._last_activity_time = base_time - timedelta(hours=2)
    coordinator._rate_limited_count = 0

    # Freeze time to ensure consistent testing
    with patch(
        "homeassistant.components.habitica.coordinators.user.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value = base_time
        coordinator._adjust_polling_for_activity()

    # Should set interval to 120 seconds for very low activity
    assert coordinator._update_interval == timedelta(seconds=120)


@pytest.mark.usefixtures("habitica")
async def test_adjust_polling_for_activity_moderate_low_activity(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test _adjust_polling_for_activity with moderate-low activity (30min-1hr ago)."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator: HabiticaDataUpdateCoordinator = config_entry.runtime_data

    # Set last activity time to 45 minutes ago (between 30min and 1 hour)
    base_time = datetime.now(UTC)
    coordinator._last_activity_time = base_time - timedelta(minutes=45)
    coordinator._rate_limited_count = 0

    with patch(
        "homeassistant.components.habitica.coordinators.user.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value = base_time
        coordinator._adjust_polling_for_activity()

    # Should set interval to 60 seconds for moderate-low activity
    assert coordinator._update_interval == timedelta(seconds=60)


@pytest.mark.usefixtures("habitica")
async def test_adjust_polling_for_activity_when_rate_limited(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test _adjust_polling_for_activity doesn't change interval when rate limited."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator: HabiticaDataUpdateCoordinator = config_entry.runtime_data

    # Set up rate limited state
    original_interval = timedelta(seconds=30)
    coordinator._update_interval = original_interval
    coordinator._last_activity_time = datetime.now(UTC) - timedelta(hours=2)
    coordinator._rate_limited_count = 1  # Simulate rate limiting

    base_time = datetime.now(UTC)
    with patch(
        "homeassistant.components.habitica.coordinators.user.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value = base_time
        coordinator._adjust_polling_for_activity()

    # Should NOT change interval when rate limited
    assert coordinator._update_interval == original_interval


@pytest.mark.usefixtures("habitica")
async def test_adjust_polling_for_activity_no_last_activity(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Test _adjust_polling_for_activity when _last_activity_time is None."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator: HabiticaDataUpdateCoordinator = config_entry.runtime_data

    # Set last activity time to None
    original_interval = timedelta(seconds=30)
    coordinator._update_interval = original_interval
    coordinator._last_activity_time = None
    coordinator._rate_limited_count = 0

    coordinator._adjust_polling_for_activity()

    # Should NOT change interval when no activity tracked
    assert coordinator._update_interval == original_interval
