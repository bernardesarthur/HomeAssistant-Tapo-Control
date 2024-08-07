from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ENABLE_MEDIA_SYNC, LOGGER
from .tapo.entities import TapoSensorEntity

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    LOGGER.debug("Setting up sensors")
    entry = hass.data[DOMAIN][config_entry.entry_id]

    async def setupEntities(entry):
        sensors = []

        if (
            "camData" in entry
            and "basic_info" in entry["camData"]
            and "battery_percent" in entry["camData"]["basic_info"]
        ):
            LOGGER.debug("Adding tapoBatterySensor...")
            sensors.append(TapoBatterySensor(entry, hass, entry))

        if (
            "camData" in entry
            and "connectionInformation" in entry["camData"]
            and entry["camData"]["connectionInformation"] is not False
            and "ssid" in entry["camData"]["connectionInformation"]
        ):
            LOGGER.debug("Adding TapoSSIDSensor...")
            sensors.append(TapoSSIDSensor(entry, hass, entry))

        if (
            "camData" in entry
            and "connectionInformation" in entry["camData"]
            and entry["camData"]["connectionInformation"] is not False
            and "link_type" in entry["camData"]["connectionInformation"]
        ):
            LOGGER.debug("Adding TapoLinkTypeSensor...")
            sensors.append(TapoLinkTypeSensor(entry, hass, entry))

        if (
            "camData" in entry
            and "connectionInformation" in entry["camData"]
            and entry["camData"]["connectionInformation"] is not False
            and "rssiValue" in entry["camData"]["connectionInformation"]
        ):
            LOGGER.debug("Adding TapoRSSISensor...")
            sensors.append(TapoRSSISensor(entry, hass, entry))

        if (
            "camData" in entry
            and "sdCardData" in entry["camData"]
            and len(entry["camData"]["sdCardData"]) > 0
        ):
            for hdd in entry["camData"]["sdCardData"]:
                for sensorProperty in hdd:
                    LOGGER.debug(
                        f"Adding TapoHDDSensor for disk {hdd['disk_name']} and property {sensorProperty}..."
                    )
                    sensors.append(
                        TapoHDDSensor(
                            entry, hass, entry, hdd["disk_name"], sensorProperty
                        )
                    )

        sensors.append(TapoSyncSensor(entry, hass, config_entry))

        return sensors

    sensors = await setupEntities(entry)
    for childDevice in entry["childDevices"]:
        sensors.extend(await setupEntities(childDevice))

    async_add_entities(sensors)


class TapoRSSISensor(TapoSensorEntity):
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT

    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self._attr_options = None
        self._attr_current_option = None
        TapoSensorEntity.__init__(
            self,
            "RSSI",
            entry,
            hass,
            config_entry,
            "mdi:signal-variant",
            None,
        )

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    async def async_update(self) -> None:
        await self._coordinator.async_request_refresh()

    def updateTapo(self, camData):
        if (
            not camData
            or camData["connectionInformation"] is False
            or "rssiValue" not in camData["connectionInformation"]
        ):
            self._attr_state = "unavailable"
        else:
            self._attr_state = camData["connectionInformation"]["rssiValue"]


class TapoLinkTypeSensor(TapoSensorEntity):
    _attr_device_class: SensorDeviceClass = None
    _attr_state_class: SensorStateClass = None
    _attr_native_unit_of_measurement = None

    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self._attr_options = None
        self._attr_current_option = None
        TapoSensorEntity.__init__(
            self,
            "Link Type",
            entry,
            hass,
            config_entry,
            "mdi:connection",
            None,
        )

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    async def async_update(self) -> None:
        await self._coordinator.async_request_refresh()

    def updateTapo(self, camData):
        if (
            not camData
            or camData["connectionInformation"] is False
            or "link_type" not in camData["connectionInformation"]
        ):
            self._attr_state = "unavailable"
        else:
            self._attr_state = camData["connectionInformation"]["link_type"]


class TapoSSIDSensor(TapoSensorEntity):
    _attr_device_class: SensorDeviceClass = None
    _attr_state_class: SensorStateClass = None
    _attr_native_unit_of_measurement = None

    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self._attr_current_option = None
        TapoSensorEntity.__init__(
            self,
            "Network SSID",
            entry,
            hass,
            config_entry,
            "mdi:wifi",
            None,
        )

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    async def async_update(self) -> None:
        await self._coordinator.async_request_refresh()

    def updateTapo(self, camData):
        if (
            not camData
            or camData["connectionInformation"] is False
            or "ssid" not in camData["connectionInformation"]
        ):
            self._attr_state = "unavailable"
        else:
            self._attr_state = camData["connectionInformation"]["ssid"]


class TapoBatterySensor(TapoSensorEntity):
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.BATTERY
    _attr_state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self._attr_current_option = None
        TapoSensorEntity.__init__(
            self,
            "Battery",
            entry,
            hass,
            config_entry,
            "mdi:battery",
            SensorDeviceClass.BATTERY,
        )

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    async def async_update(self) -> None:
        await self._coordinator.async_request_refresh()

    def updateTapo(self, camData):
        if not camData:
            self._attr_state = "unavailable"
        else:
            self._attr_state = camData["basic_info"]["battery_percent"]


class TapoHDDSensor(TapoSensorEntity):
    _attr_device_class: SensorDeviceClass = None
    _attr_state_class: SensorStateClass = None
    _attr_native_unit_of_measurement = None

    def __init__(
        self, entry: dict, hass: HomeAssistant, config_entry, sensorName, sensorProperty
    ):
        self._attr_options = None
        self._attr_current_option = None
        self._sensor_name = sensorName
        self._sensor_property = sensorProperty
        TapoSensorEntity.__init__(
            self,
            f"Disk {sensorName} {sensorProperty}",
            entry,
            hass,
            config_entry,
            "mdi:sd",
            None,
        )

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    async def async_update(self) -> None:
        await self._coordinator.async_request_refresh()

    def updateTapo(self, camData):
        state = STATE_UNAVAILABLE
        if camData and "sdCardData" in camData and len(camData["sdCardData"]) > 0:
            for hdd in camData["sdCardData"]:
                if hdd["disk_name"] == self._sensor_name:
                    state = hdd[self._sensor_property]
        self._attr_state = state


class TapoSyncSensor(TapoSensorEntity):
    _attr_device_class: SensorDeviceClass = None
    _attr_state_class: SensorStateClass = None
    _attr_native_unit_of_measurement = None

    def __init__(self, entry: dict, hass: HomeAssistant, config_entry):
        self._attr_options = None
        self._attr_current_option = None
        TapoSensorEntity.__init__(
            self,
            "Recordings Synchronization",
            entry,
            hass,
            config_entry,
            None,
            None,
        )

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    async def async_update(self) -> None:
        await self._coordinator.async_request_refresh()

    def updateTapo(self, camData):
        enableMediaSync = self._config_entry.data.get(ENABLE_MEDIA_SYNC)
        LOGGER.debug(f"Enable Media Sync: {enableMediaSync}")
        if enableMediaSync:
            LOGGER.debug(
                f"Initial Media Scan: {self._hass.data[DOMAIN][self._config_entry.entry_id]['initialMediaScanDone']}"
            )
            LOGGER.debug(
                f"Media Sync Available: {self._hass.data[DOMAIN][self._config_entry.entry_id]['mediaSyncAvailable']}"
            )
            LOGGER.debug(
                f"Download Progress: {self._hass.data[DOMAIN][self._config_entry.entry_id]['downloadProgress']}"
            )
            LOGGER.debug(
                f"Running media sync: {self._hass.data[DOMAIN][self._config_entry.entry_id]['runningMediaSync']}"
            )
            LOGGER.debug(
                f"Media Sync Schedueled: {self._hass.data[DOMAIN][self._config_entry.entry_id]['mediaSyncScheduled']}"
            )
            LOGGER.debug(
                f"Media Sync Ran Once: {self._hass.data[DOMAIN][self._config_entry.entry_id]['mediaSyncRanOnce']}"
            )

            if not self._hass.data[DOMAIN][self._config_entry.entry_id][
                "initialMediaScanDone"
            ] or (
                self._hass.data[DOMAIN][self._config_entry.entry_id][
                    "initialMediaScanDone"
                ]
                and not self._hass.data[DOMAIN][self._config_entry.entry_id][
                    "mediaSyncRanOnce"
                ]
            ):
                self._attr_state = "Starting"
            elif not self._hass.data[DOMAIN][self._config_entry.entry_id][
                "mediaSyncAvailable"
            ]:
                self._attr_state = "No Recordings Found"
            elif self._hass.data[DOMAIN][self._config_entry.entry_id][
                "downloadProgress"
            ]:
                if (
                    self._hass.data[DOMAIN][self._config_entry.entry_id][
                        "downloadProgress"
                    ]
                    == "Finished download"
                ):
                    self._attr_state = "Idle"
                else:
                    self._attr_state = self._hass.data[DOMAIN][
                        self._config_entry.entry_id
                    ]["downloadProgress"]
            else:
                self._attr_state = "Idle"
        else:
            self._attr_state = "Idle"
