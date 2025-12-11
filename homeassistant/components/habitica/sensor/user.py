"""Base user sensor classes for Habitica integration."""

from __future__ import annotations

from datetime import datetime

from habiticalib import HabiticaClass, ha

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import StateType

from ..const import ASSETS_URL
from ..entity import HabiticaBase, HabiticaPartyMemberBase
from .descriptions import HabiticaSensorEntity, HabiticaSensorEntityDescription

SVG_CLASS = {
    HabiticaClass.WARRIOR: ha.WARRIOR,
    HabiticaClass.ROGUE: ha.ROGUE,
    HabiticaClass.MAGE: ha.WIZARD,
    HabiticaClass.HEALER: ha.HEALER,
}


class HabiticaSensor(HabiticaBase, SensorEntity):  # pylint: disable=hass-enforce-class-module
    """A generic Habitica sensor."""

    entity_description: HabiticaSensorEntityDescription

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the device."""

        return (
            self.entity_description.value_fn(self.user, self.coordinator.content)
            if self.user is not None
            else None
        )

    @property
    def extra_state_attributes(self) -> dict[str, float | None] | None:
        """Return entity specific state attributes."""
        if self.user is not None and (func := self.entity_description.attributes_fn):
            return func(self.user, self.coordinator.content)
        return None

    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture to use in the frontend, if any."""
        if (
            self.entity_description.key is HabiticaSensorEntity.CLASS
            and self.user is not None
            and (_class := self.user.stats.Class)
        ):
            return SVG_CLASS[_class]

        if (
            self.entity_description.key is HabiticaSensorEntity.DISPLAY_NAME
            and self.user is not None
            and (img_url := self.user.profile.imageUrl)
        ):
            return img_url

        if entity_picture := self.entity_description.entity_picture:
            return (
                entity_picture
                if entity_picture.startswith("data:image")
                else f"{ASSETS_URL}{entity_picture}"
            )

        return None


class HabiticaPartyMemberSensor(HabiticaSensor, HabiticaPartyMemberBase):  # pylint: disable=hass-enforce-class-module
    """Habitica party member sensor."""
