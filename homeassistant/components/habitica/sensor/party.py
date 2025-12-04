"""Party sensor for Habitica integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import StateType

from ..const import ASSETS_URL
from ..entity import HabiticaPartyBase
from .descriptions import HabiticaPartySensorEntityDescription


class HabiticaPartySensor(HabiticaPartyBase, SensorEntity):  # pylint: disable=hass-enforce-class-module
    """Habitica party sensor."""

    entity_description: HabiticaPartySensorEntityDescription

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the device."""

        return self.entity_description.value_fn(
            self.coordinator.data.party, self.content
        )

    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture to use in the frontend, if any."""
        pic = self.entity_description.entity_picture

        entity_picture = (
            pic
            if isinstance(pic, str) or pic is None
            else pic(self.coordinator.data.party)
        )

        return (
            None
            if not entity_picture
            else entity_picture
            if entity_picture.startswith("data:image")
            else f"{ASSETS_URL}{entity_picture}"
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if func := self.entity_description.attributes_fn:
            return func(self.coordinator.data.party, self.content)
        return None
