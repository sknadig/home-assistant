"""Support for Modbus Coil and Discrete Input sensors."""
import logging
from typing import Optional

import voluptuous as vol

from homeassistant.components.binary_sensor import (
    DEVICE_CLASSES_SCHEMA,
    PLATFORM_SCHEMA,
    BinarySensorDevice,
)
from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME, CONF_SLAVE
from homeassistant.helpers import config_validation as cv

from . import CONF_HUB, DEFAULT_HUB, DOMAIN as MODBUS_DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_DEPRECATED_COIL = "coil"
CONF_DEPRECATED_COILS = "coils"

CONF_INPUTS = "inputs"
CONF_INPUT_TYPE = "input_type"
CONF_ADDRESS = "address"

INPUT_TYPE_COIL = "coil"
INPUT_TYPE_DISCRETE = "discrete_input"

PLATFORM_SCHEMA = vol.All(
    cv.deprecated(CONF_DEPRECATED_COILS, CONF_INPUTS),
    PLATFORM_SCHEMA.extend(
        {
            vol.Required(CONF_INPUTS): [
                vol.All(
                    cv.deprecated(CONF_DEPRECATED_COIL, CONF_ADDRESS),
                    vol.Schema(
                        {
                            vol.Required(CONF_ADDRESS): cv.positive_int,
                            vol.Required(CONF_NAME): cv.string,
                            vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
                            vol.Optional(CONF_HUB, default=DEFAULT_HUB): cv.string,
                            vol.Optional(CONF_SLAVE): cv.positive_int,
                            vol.Optional(
                                CONF_INPUT_TYPE, default=INPUT_TYPE_COIL
                            ): vol.In([INPUT_TYPE_COIL, INPUT_TYPE_DISCRETE]),
                        }
                    ),
                )
            ]
        }
    ),
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Modbus binary sensors."""
    sensors = []
    for entry in config.get(CONF_INPUTS):
        hub = hass.data[MODBUS_DOMAIN][entry.get(CONF_HUB)]
        sensors.append(
            ModbusBinarySensor(
                hub,
                entry.get(CONF_NAME),
                entry.get(CONF_SLAVE),
                entry.get(CONF_ADDRESS),
                entry.get(CONF_DEVICE_CLASS),
                entry.get(CONF_INPUT_TYPE),
            )
        )

    add_entities(sensors)


class ModbusBinarySensor(BinarySensorDevice):
    """Modbus binary sensor."""

    def __init__(self, hub, name, slave, address, device_class, input_type):
        """Initialize the Modbus binary sensor."""
        self._hub = hub
        self._name = name
        self._slave = int(slave) if slave else None
        self._address = int(address)
        self._device_class = device_class
        self._input_type = input_type
        self._value = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self._value

    @property
    def device_class(self) -> Optional[str]:
        """Return the device class of the sensor."""
        return self._device_class

    def update(self):
        """Update the state of the sensor."""
        if self._input_type == INPUT_TYPE_COIL:
            result = self._hub.read_coils(self._slave, self._address, 1)
        else:
            result = self._hub.read_discrete_inputs(self._slave, self._address, 1)
        try:
            self._value = result.bits[0]
        except AttributeError:
            _LOGGER.error(
                "No response from hub %s, slave %s, address %s",
                self._hub.name,
                self._slave,
                self._address,
            )
