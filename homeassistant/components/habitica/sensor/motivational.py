"""Motivational sensor for Habitica integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinators import HabiticaDataUpdateCoordinator
from .utils import get_daily_motivational_prompt


class HabiticaMotivationalSensor(  # pylint: disable=hass-enforce-class-module
    CoordinatorEntity[HabiticaDataUpdateCoordinator], SensorEntity
):
    """Sensor for daily motivational messages."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: HabiticaDataUpdateCoordinator,
    ) -> None:
        """Initialize the motivational sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_daily_motivation"
        self._attr_name = "Habitica Daily Motivation"
        self._attr_translation_key = "motivational_prompt"

        # Set device info to link to the main Habitica device
        assert coordinator.config_entry.unique_id is not None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.unique_id)},
        )

    @property
    def native_value(self) -> StateType:
        """Return the motivational message."""
        if not self.coordinator.data or not self.coordinator.data.user:
            return "Ready to build great habits today!"

        return get_daily_motivational_prompt(
            self.coordinator.data.user, self.coordinator.content
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return user stats for context."""
        if not self.coordinator.data or not self.coordinator.data.user:
            return {}

        user = self.coordinator.data.user
        return {
            "level": user.stats.lvl,
            "class": user.stats.Class.value if user.stats.Class else None,
        }
