"""Test Habitica sensor platform."""

from collections.abc import Generator
from datetime import timedelta
from unittest.mock import AsyncMock, patch

from freezegun.api import FrozenDateTimeFactory
from habiticalib import HabiticaTasksResponse
import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.habitica.const import DATA_HABIT_SENSORS, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import (
    MockConfigEntry,
    async_fire_time_changed,
    load_fixture,
    snapshot_platform,
)


@pytest.fixture(autouse=True)
def sensor_only() -> Generator[None]:
    """Enable only the sensor platform."""
    with patch(
        "homeassistant.components.habitica.PLATFORMS",
        [Platform.SENSOR],
    ):
        yield


@pytest.mark.usefixtures("habitica", "entity_registry_enabled_by_default")
@pytest.mark.freeze_time("2024-09-18 00:00:00+00:00")
async def test_sensors(
    hass: HomeAssistant,
    config_entry_with_subentry: MockConfigEntry,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test setup of the Habitica sensor platform."""

    # Mock random.choice to return consistent motivational message
    with patch(
        "homeassistant.components.habitica.sensor.utils.random.choice"
    ) as mock_choice:
        mock_choice.return_value = (
            "🚀 Your future self will thank you for what you do today!"
        )

        config_entry_with_subentry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry_with_subentry.entry_id)
        await hass.async_block_till_done()

        assert config_entry_with_subentry.state is ConfigEntryState.LOADED

        await snapshot_platform(
            hass, entity_registry, snapshot, config_entry_with_subentry.entry_id
        )


@pytest.mark.usefixtures("habitica")
async def test_habit_sensor_removal(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    habitica: AsyncMock,
    freezer: FrozenDateTimeFactory,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test habit sensors are removed when habit is deleted."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    # Verify initial habit sensor exists
    habit_sensor_id = "sensor.gesundes_essen_junkfood"
    assert hass.states.get(habit_sensor_id) is not None
    assert entity_registry.async_get(habit_sensor_id) is not None

    # Mock get_tasks to return tasks without the first habit for future calls
    def mock_get_tasks_without_habit(task_type=None):
        """Mock tasks without first habit."""
        if task_type:
            return HabiticaTasksResponse.from_json(
                load_fixture("completed_todos.json", DOMAIN)
            )
        # Return tasks without the first habit
        tasks_data = HabiticaTasksResponse.from_json(load_fixture("tasks.json", DOMAIN))
        # Filter out the first habit
        tasks_data.data = [
            task
            for task in tasks_data.data
            if task.id != "f21fa608-cfc6-4413-9fc7-0eb1b48ca43a"
        ]
        return tasks_data

    habitica.get_tasks.side_effect = mock_get_tasks_without_habit

    # Trigger coordinator update
    freezer.tick(timedelta(seconds=60))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Verify habit sensor is removed from entity registry
    assert entity_registry.async_get(habit_sensor_id) is None


@pytest.mark.usefixtures("habitica")
async def test_habit_sensor_optimistic_update_up(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Test habit sensor optimistic update with 'up' direction."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    # Get habit sensor
    habit_sensor_id = "sensor.gesundes_essen_junkfood"
    state = hass.states.get(habit_sensor_id)
    assert state is not None
    initial_value = float(state.state)
    initial_counter_up = state.attributes["counter_up"]
    initial_counter_down = state.attributes["counter_down"]

    # Get the habit sensor entity
    config_entry_id = config_entry.entry_id
    habit_id = "f21fa608-cfc6-4413-9fc7-0eb1b48ca43a"
    habit_sensor = hass.data[DATA_HABIT_SENSORS][config_entry_id][habit_id]

    # Set optimistic update with direction "up"
    value_delta = 0.5
    habit_sensor.set_optimistic_update(value_delta, "up")

    # Verify optimistic value is set
    state = hass.states.get(habit_sensor_id)
    assert state is not None
    expected_value = round(initial_value + value_delta, 2)
    assert float(state.state) == expected_value
    assert state.attributes["counter_up"] == initial_counter_up + 1
    assert state.attributes["counter_down"] == initial_counter_down


@pytest.mark.usefixtures("habitica")
async def test_habit_sensor_optimistic_update_down(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Test habit sensor optimistic update with 'down' direction."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    # Get habit sensor
    habit_sensor_id = "sensor.gesundes_essen_junkfood"
    state = hass.states.get(habit_sensor_id)
    assert state is not None
    initial_value = float(state.state)
    initial_counter_up = state.attributes["counter_up"]
    initial_counter_down = state.attributes["counter_down"]

    # Get the habit sensor entity
    config_entry_id = config_entry.entry_id
    habit_id = "f21fa608-cfc6-4413-9fc7-0eb1b48ca43a"
    habit_sensor = hass.data[DATA_HABIT_SENSORS][config_entry_id][habit_id]

    # Set optimistic update with direction "down"
    value_delta = -0.3
    habit_sensor.set_optimistic_update(value_delta, "down")

    # Verify optimistic value is set
    state = hass.states.get(habit_sensor_id)
    assert state is not None
    expected_value = round(initial_value + value_delta, 2)
    assert float(state.state) == expected_value
    assert state.attributes["counter_up"] == initial_counter_up
    assert state.attributes["counter_down"] == initial_counter_down + 1


@pytest.mark.usefixtures("habitica")
async def test_habit_sensor_optimistic_update_no_current_habit(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    habitica: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test habit sensor optimistic update when current habit is None."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    # Get the habit sensor entity
    config_entry_id = config_entry.entry_id
    habit_id = "f21fa608-cfc6-4413-9fc7-0eb1b48ca43a"
    habit_sensor = hass.data[DATA_HABIT_SENSORS][config_entry_id][habit_id]

    # Mock get_tasks to return tasks without this habit
    def mock_get_tasks_without_habit(task_type=None):
        """Mock tasks without the habit."""
        if task_type:
            return HabiticaTasksResponse.from_json(
                load_fixture("completed_todos.json", DOMAIN)
            )
        tasks_data = HabiticaTasksResponse.from_json(load_fixture("tasks.json", DOMAIN))
        tasks_data.data = [task for task in tasks_data.data if task.id != habit_id]
        return tasks_data

    habitica.get_tasks.side_effect = mock_get_tasks_without_habit

    # Trigger coordinator update to remove habit from data
    freezer.tick(timedelta(seconds=60))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Try to set optimistic update when current_habit is None
    # This should not raise an exception, just do nothing
    habit_sensor.set_optimistic_update(0.5, "up")

    # Verify optimistic values are not set (should remain None)
    assert habit_sensor._optimistic_value is None
    assert habit_sensor._optimistic_counter_up is None
    assert habit_sensor._optimistic_counter_down is None


@pytest.mark.usefixtures("habitica")
async def test_habit_sensor_extra_state_attributes_no_current_habit(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    habitica: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test habit sensor extra_state_attributes when current habit is None."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    # Get the habit sensor entity
    config_entry_id = config_entry.entry_id
    habit_id = "f21fa608-cfc6-4413-9fc7-0eb1b48ca43a"
    habit_sensor = hass.data[DATA_HABIT_SENSORS][config_entry_id][habit_id]

    # Mock get_tasks to return empty coordinator data
    def mock_get_tasks_empty(task_type=None):
        """Mock empty tasks response."""
        if task_type:
            return HabiticaTasksResponse.from_json(
                load_fixture("completed_todos.json", DOMAIN)
            )
        tasks_data = HabiticaTasksResponse.from_json(load_fixture("tasks.json", DOMAIN))
        tasks_data.data = []
        return tasks_data

    habitica.get_tasks.side_effect = mock_get_tasks_empty

    # Trigger coordinator update
    freezer.tick(timedelta(seconds=60))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Get extra state attributes when current_habit is None
    attributes = habit_sensor.extra_state_attributes
    assert attributes == {}


@pytest.mark.usefixtures("habitica")
async def test_habit_sensor_extra_state_attributes_with_optimistic_counters(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Test habit sensor extra_state_attributes uses optimistic counters."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    # Get habit sensor
    habit_sensor_id = "sensor.gesundes_essen_junkfood"
    state = hass.states.get(habit_sensor_id)
    assert state is not None
    initial_counter_up = state.attributes["counter_up"]
    initial_counter_down = state.attributes["counter_down"]

    # Get the habit sensor entity
    config_entry_id = config_entry.entry_id
    habit_id = "f21fa608-cfc6-4413-9fc7-0eb1b48ca43a"
    habit_sensor = hass.data[DATA_HABIT_SENSORS][config_entry_id][habit_id]

    # Set optimistic update
    habit_sensor.set_optimistic_update(0.5, "up")

    # Verify extra_state_attributes uses optimistic counters
    attributes = habit_sensor.extra_state_attributes
    assert attributes["counter_up"] == initial_counter_up + 1
    assert attributes["counter_down"] == initial_counter_down


@pytest.mark.usefixtures("habitica")
async def test_habit_sensor_handle_coordinator_update_clears_optimistic(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test _handle_coordinator_update clears optimistic values."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    # Get the habit sensor entity
    config_entry_id = config_entry.entry_id
    habit_id = "f21fa608-cfc6-4413-9fc7-0eb1b48ca43a"
    habit_sensor = hass.data[DATA_HABIT_SENSORS][config_entry_id][habit_id]

    # Set optimistic values
    habit_sensor.set_optimistic_update(0.5, "up")

    # Verify optimistic values are set
    assert habit_sensor._optimistic_value is not None
    assert habit_sensor._optimistic_counter_up is not None
    assert habit_sensor._optimistic_counter_down is not None

    # Trigger coordinator update
    freezer.tick(timedelta(seconds=60))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Verify optimistic values are cleared
    assert habit_sensor._optimistic_value is None
    assert habit_sensor._optimistic_counter_up is None
    assert habit_sensor._optimistic_counter_down is None


@pytest.mark.usefixtures("habitica")
async def test_frequency_sensor_default_frequency_native_value(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    habitica: AsyncMock,
) -> None:
    """Test frequency sensor native_value with default frequency (None -> daily)."""

    # Mock get_tasks to return habits where one has None frequency
    def mock_get_tasks_with_none_frequency(task_type=None):
        """Mock tasks with a habit having None frequency."""
        if task_type:
            return HabiticaTasksResponse.from_json(
                load_fixture("completed_todos.json", DOMAIN)
            )
        tasks_data = HabiticaTasksResponse.from_json(load_fixture("tasks.json", DOMAIN))
        # Set the first task's (a habit) frequency to None (should default to daily)
        if tasks_data.data:
            tasks_data.data[0].frequency = None
        return tasks_data

    habitica.get_tasks.side_effect = mock_get_tasks_with_none_frequency

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    # Get the daily frequency sensor
    daily_sensor = hass.states.get("sensor.habits_daily")
    assert daily_sensor is not None

    # The fixture has 2 habits displayed (from what gets loaded into coordinator)
    # We set the first one's frequency to None, so it should still count as daily (default behavior)
    # Result: still 2 daily habits (one with daily frequency, one with None defaulting to daily)
    assert int(daily_sensor.state) == 2


@pytest.mark.usefixtures("habitica")
async def test_frequency_sensor_default_frequency_extra_state_attributes(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    habitica: AsyncMock,
) -> None:
    """Test frequency sensor extra_state_attributes with default frequency."""

    # Mock get_tasks to return a habit with None frequency
    def mock_get_tasks_with_none_frequency(task_type=None):
        """Mock tasks with a habit having None frequency."""
        if task_type:
            return HabiticaTasksResponse.from_json(
                load_fixture("completed_todos.json", DOMAIN)
            )
        tasks_data = HabiticaTasksResponse.from_json(load_fixture("tasks.json", DOMAIN))
        # Set the first task's (a habit) frequency to None (should default to daily)
        if tasks_data.data:
            tasks_data.data[0].frequency = None
        return tasks_data

    habitica.get_tasks.side_effect = mock_get_tasks_with_none_frequency

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    # Get the daily frequency sensor
    daily_sensor = hass.states.get("sensor.habits_daily")
    assert daily_sensor is not None

    # Check extra_state_attributes includes our habit with None frequency
    attributes = daily_sensor.attributes
    assert "habits" in attributes
    assert "total_habits" in attributes
    assert "frequency" in attributes
    assert attributes["frequency"] == "daily"

    # The fixture loads 2 habits, and we set the first one's frequency to None
    # It should still appear in the daily habits list (defaulting to daily)
    assert len(attributes["habits"]) == 2

    # Verify the first habit (with None frequency) is in the list
    first_habit = attributes["habits"][0]
    assert "id" in first_habit
    assert "text" in first_habit
    assert "value" in first_habit
