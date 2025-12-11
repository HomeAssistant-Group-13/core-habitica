"""Habit sensor for Habitica integration."""

from __future__ import annotations

from typing import Any

from habiticalib import TaskData

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DATA_HABIT_SENSORS, DOMAIN
from ..coordinators import HabiticaDataUpdateCoordinator


class HabiticaHabitSensor(  # pylint: disable=hass-enforce-class-module
    CoordinatorEntity[HabiticaDataUpdateCoordinator], SensorEntity
):
    """Sensor for individual Habitica habits."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: HabiticaDataUpdateCoordinator,
        habit: TaskData,
    ) -> None:
        """Initialize the habit sensor."""
        super().__init__(coordinator)
        self.habit = habit
        self.habit_id = str(habit.id)
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_habit_{habit.id}"
        self._attr_name = habit.text
        self._optimistic_value: float | None = None
        self._optimistic_counter_up: int | None = None
        self._optimistic_counter_down: int | None = None

        # Set device info to link to the main Habitica device
        assert coordinator.config_entry.unique_id is not None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.unique_id)},
        )

    def _get_current_habit(self) -> TaskData | None:
        """Get current habit data from coordinator."""
        if self.coordinator.data and self.coordinator.data.habits:
            for habit in self.coordinator.data.habits:
                if habit and habit.id == self.habit.id:
                    return habit
        return None

    def set_optimistic_update(self, value_delta: float, direction: str) -> None:
        """Set optimistic value for immediate UI feedback."""
        current_habit = self._get_current_habit()
        if current_habit:
            # Set optimistic value
            current_value = current_habit.value if current_habit.value else 0
            self._optimistic_value = round(current_value + value_delta, 2)

            # Set optimistic counters
            if direction == "up":
                self._optimistic_counter_up = (current_habit.counterUp or 0) + 1
                self._optimistic_counter_down = current_habit.counterDown or 0
            else:
                self._optimistic_counter_up = current_habit.counterUp or 0
                self._optimistic_counter_down = (current_habit.counterDown or 0) + 1

            # Trigger state update
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()

        # Register this sensor in hass.data for button lookup
        config_entry_id = self.coordinator.config_entry.entry_id
        if DATA_HABIT_SENSORS in self.hass.data:
            if config_entry_id in self.hass.data[DATA_HABIT_SENSORS]:
                self.hass.data[DATA_HABIT_SENSORS][config_entry_id][self.habit_id] = (
                    self
                )

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        await super().async_will_remove_from_hass()

        # Unregister this sensor
        config_entry_id = self.coordinator.config_entry.entry_id
        if (
            DATA_HABIT_SENSORS in self.hass.data
            and config_entry_id in self.hass.data[DATA_HABIT_SENSORS]
            and self.habit_id in self.hass.data[DATA_HABIT_SENSORS][config_entry_id]
        ):
            del self.hass.data[DATA_HABIT_SENSORS][config_entry_id][self.habit_id]

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Clear optimistic values when real data arrives
        self._optimistic_value = None
        self._optimistic_counter_up = None
        self._optimistic_counter_down = None
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> StateType:
        """Return the habit value."""
        # Return optimistic value if set (for immediate UI feedback)
        if self._optimistic_value is not None:
            return self._optimistic_value

        # Find the current habit data from coordinator
        current_habit = self._get_current_habit()
        if current_habit:
            return round(current_habit.value, 2) if current_habit.value else 0
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return habit specific attributes."""
        current_habit = self._get_current_habit()
        if current_habit:
            # Use optimistic counters if available for immediate UI feedback
            counter_up = (
                self._optimistic_counter_up
                if self._optimistic_counter_up is not None
                else (current_habit.counterUp or 0)
            )
            counter_down = (
                self._optimistic_counter_down
                if self._optimistic_counter_down is not None
                else (current_habit.counterDown or 0)
            )

            return {
                "habit_id": str(current_habit.id),
                "text": current_habit.text,
                "notes": current_habit.notes or "",
                "counter_up": counter_up,
                "counter_down": counter_down,
                "frequency": current_habit.frequency.value
                if current_habit.frequency
                else "daily",
                "up": current_habit.up if hasattr(current_habit, "up") else True,
                "down": current_habit.down if hasattr(current_habit, "down") else True,
            }
        return {}
