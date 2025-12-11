"""Frequency analysis sensors for Habitica integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinators import HabiticaDataUpdateCoordinator


class HabiticaFrequencySensor(  # pylint: disable=hass-enforce-class-module
    CoordinatorEntity[HabiticaDataUpdateCoordinator], SensorEntity
):
    """Sensor for habit frequency analysis."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: HabiticaDataUpdateCoordinator,
        frequency_type: str,
    ) -> None:
        """Initialize the frequency sensor."""
        super().__init__(coordinator)
        self.frequency_type = frequency_type
        self._attr_unique_id = (
            f"{coordinator.config_entry.unique_id}_habits_{frequency_type}"
        )
        self._attr_name = f"Habits {frequency_type.title()}"
        self._attr_translation_key = f"habits_{frequency_type}"

        # Set device info to link to the main Habitica device
        assert coordinator.config_entry.unique_id is not None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.unique_id)},
        )

    @property
    def native_value(self) -> StateType:
        """Return the habit count for this frequency."""
        if not self.coordinator.data or not self.coordinator.data.habits:
            return 0

        count = 0
        for habit in self.coordinator.data.habits:
            if habit and habit.frequency:
                habit_frequency = habit.frequency.value.lower()
                if habit_frequency == self.frequency_type:
                    count += 1
            elif self.frequency_type == "daily":
                # Default frequency is daily if not specified
                count += 1

        return count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return frequency specific attributes."""
        if not self.coordinator.data or not self.coordinator.data.habits:
            return {"habits": [], "total_habits": 0}

        habits_list = []
        total_habits = len(self.coordinator.data.habits)

        for habit in self.coordinator.data.habits:
            if habit and habit.frequency:
                habit_frequency = habit.frequency.value.lower()
                if habit_frequency == self.frequency_type:
                    habits_list.append(
                        {
                            "id": str(habit.id),
                            "text": habit.text,
                            "value": round(habit.value, 2) if habit.value else 0,
                        }
                    )
            elif self.frequency_type == "daily" and habit:
                # Default frequency is daily if not specified
                habits_list.append(
                    {
                        "id": str(habit.id),
                        "text": habit.text,
                        "value": round(habit.value, 2) if habit.value else 0,
                    }
                )

        return {
            "habits": habits_list,
            "total_habits": total_habits,
            "frequency": self.frequency_type,
        }
