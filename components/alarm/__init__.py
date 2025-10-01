# components/alarm/__init__.py
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import (
    CONF_ID,
    CONF_HOUR,
    CONF_MINUTE,
    CONF_CONDITION,
)

# External deps
time_ns = cg.esphome_ns.namespace("time")
rtttl_ns = cg.esphome_ns.namespace("rtttl")
binary_sensor_ns = cg.esphome_ns.namespace("binary_sensor")

# Our namespace
alarm_ns = cg.esphome_ns.namespace("alarm")
Alarm = alarm_ns.class_("Alarm", cg.Component)

CONF_TIME_ID = "time_id"
CONF_RTTTL_ID = "rtttl_id"
CONF_ACTIVE_SENSOR = "active_sensor"
CONF_SNOOZED_SENSOR = "snoozed_sensor"
CONF_RTTTL_SEQUENCE = "rtttl_sequence"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(Alarm),
        cv.GenerateID(CONF_TIME_ID): cv.use_id(time_ns.RealTimeClock),
        cv.GenerateID(CONF_RTTTL_ID): cv.use_id(rtttl_ns.RTTTL),
        cv.Required(CONF_HOUR): cv.int_range(min=0, max=23),
        cv.Required(CONF_MINUTE): cv.int_range(min=0, max=59),
        cv.Required(CONF_RTTTL_SEQUENCE): cv.string_strict,
#        cv.Optional(CONF_CONDITION): cv.lambda_,
        cv.Optional(CONF_ACTIVE_SENSOR): cv.declare_id(binary_sensor_ns.BinarySensor),
        cv.Optional(CONF_SNOOZED_SENSOR): cv.declare_id(binary_sensor_ns.BinarySensor),
    }
).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    time_comp = await cg.get_variable(config[CONF_TIME_ID])
    cg.add(var.set_time_component(time_comp))

    rtttl_comp = await cg.get_variable(config[CONF_RTTTL_ID])
    cg.add(var.set_rtttl(rtttl_comp))

    cg.add(var.set_alarm_time(config[CONF_HOUR], config[CONF_MINUTE]))
    cg.add(var.set_rtttl_sequence(config[CONF_RTTTL_SEQUENCE]))

#    if CONF_CONDITION in config:
#        template_ = await cg.process_lambda(config[CONF_CONDITION])
#        cg.add(var.set_condition(template_))

    if CONF_ACTIVE_SENSOR in config:
        sens = cg.new_Pvariable(config[CONF_ACTIVE_SENSOR])
        cg.add(var.active_sensor, sens)
        await binary_sensor_ns.register_binary_sensor(sens, {})
    if CONF_SNOOZED_SENSOR in config:
        sens = cg.new_Pvariable(config[CONF_SNOOZED_SENSOR])
        cg.add(var.snoozed_sensor, sens)
        await binary_sensor_ns.register_binary_sensor(sens, {})

