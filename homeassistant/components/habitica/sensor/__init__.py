"""Habitica sensors package."""

from __future__ import annotations

import logging
from uuid import UUID

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .. import HABITICA_KEY
from ..const import DATA_HABIT_SENSORS, DOMAIN
from ..coordinators import HabiticaConfigEntry
from .descriptions import (
    SENSOR_DESCRIPTIONS,
    SENSOR_DESCRIPTIONS_COMMON,
    SENSOR_DESCRIPTIONS_PARTY,
)
from .frequency import HabiticaFrequencySensor
from .habit import HabiticaHabitSensor
from .motivational import HabiticaMotivationalSensor
from .party import HabiticaPartySensor
from .user import HabiticaPartyMemberSensor, HabiticaSensor

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1

__all__ = [
    "PARALLEL_UPDATES",
    "HabiticaFrequencySensor",
    "HabiticaHabitSensor",
    "HabiticaMotivationalSensor",
    "HabiticaPartyMemberSensor",
    "HabiticaPartySensor",
    "HabiticaSensor",
    "async_setup_entry",
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HabiticaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the habitica sensors."""

    coordinator = config_entry.runtime_data

    # Initialize habit sensor registry in hass.data
    config_entry_id = config_entry.entry_id
    if DATA_HABIT_SENSORS not in hass.data:
        hass.data[DATA_HABIT_SENSORS] = {}
    if config_entry_id not in hass.data[DATA_HABIT_SENSORS]:
        hass.data[DATA_HABIT_SENSORS][config_entry_id] = {}

    async_add_entities(
        HabiticaSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS + SENSOR_DESCRIPTIONS_COMMON
    )

    # Add individual habit sensors with dynamic management
    habits_added: set[str] = set()

    @callback
    def add_habit_sensors() -> None:
        """Add or remove habit sensors based on coordinator data."""
        nonlocal habits_added
        sensors = []
        entity_registry = er.async_get(hass)

        current_habits = set()
        if coordinator.data and coordinator.data.habits:
            for habit in coordinator.data.habits:
                if habit and habit.id:
                    habit_id = str(habit.id)
                    current_habits.add(habit_id)

                    # Add new habit sensor if not already added
                    if habit_id not in habits_added:
                        sensors.append(HabiticaHabitSensor(coordinator, habit))
                        habits_added.add(habit_id)

        # Remove sensors for habits that no longer exist
        for habit_id in habits_added.copy():
            if habit_id not in current_habits:
                if entity_id := entity_registry.async_get_entity_id(
                    SENSOR_DOMAIN,
                    DOMAIN,
                    f"{coordinator.config_entry.unique_id}_habit_{habit_id}",
                ):
                    entity_registry.async_remove(entity_id)
                habits_added.remove(habit_id)

        if sensors:
            async_add_entities(sensors)

    coordinator.async_add_listener(add_habit_sensors)
    add_habit_sensors()

    if party := coordinator.data.user.party.id:
        party_coordinator = hass.data[HABITICA_KEY][party]
        async_add_entities(
            HabiticaPartySensor(
                party_coordinator,
                config_entry,
                description,
                coordinator.content,
            )
            for description in SENSOR_DESCRIPTIONS_PARTY
        )
        for subentry_id, subentry in config_entry.subentries.items():
            if (
                subentry.unique_id
                and UUID(subentry.unique_id) in party_coordinator.data.members
            ):
                async_add_entities(
                    (
                        HabiticaPartyMemberSensor(
                            coordinator,
                            party_coordinator,
                            description,
                            subentry,
                        )
                        for description in SENSOR_DESCRIPTIONS_COMMON
                    ),
                    config_subentry_id=subentry_id,
                )

    # Add frequency sensors
    async_add_entities(
        tuple(
            HabiticaFrequencySensor(coordinator, frequency_type)
            for frequency_type in ("daily", "weekly", "monthly")
        )
    )

    # Add motivational prompt sensor
    async_add_entities((HabiticaMotivationalSensor(coordinator),))
