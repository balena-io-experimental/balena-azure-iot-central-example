# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.

import iotc
import os
from iotc import IOTConnectType, IOTLogLevel
from gpiozero import CPUTemperature, DiskUsage, LED
import time
from time import sleep

try:
    deviceId = os.environ["DEVICE_ID"]
    scopeId = os.environ["SCOPE_ID"]
    mkey = os.environ["DEVICE_KEY"]
except KeyError:
    print("Please set all the environment variables in the dashboard")
    sys.exit(1)

iotc = iotc.Device(scopeId, mkey, deviceId,
                   IOTConnectType.IOTC_CONNECT_SYMM_KEY)
iotc.setLogLevel(IOTLogLevel.IOTC_LOGGING_API_ONLY)

gCanSend = False

cpu = CPUTemperature(min_temp=40, max_temp=90)
disk = DiskUsage()
led = LED(17)

lastSent = 0
interval = 300


def onconnect(info):
    global gCanSend
    print("- [onconnect] => status:" + str(info.getStatusCode()))
    if info.getStatusCode() == 0:
        if iotc.isConnected():
            gCanSend = True


def onmessagesent(info):
    print("\t- [onmessagesent] => " + str(info.getPayload()))


def oncommand(info):
    print("- [oncommand] => " + info.getTag() +
          " => " + str(info.getPayload()))
    if info.getTag() == "led_toggle":
        print("Toggling LED state")
        led.toggle()


def onsettingsupdated(info):
    print("- [onsettingsupdated] => " +
          info.getTag() + " => " + info.getPayload())


iotc.on("ConnectionStatus", onconnect)
iotc.on("MessageSent", onmessagesent)
iotc.on("Command", oncommand)
iotc.on("SettingsUpdated", onsettingsupdated)

iotc.connect()

while iotc.isConnected():
    iotc.doNext()  # do the async work needed to be done for MQTT
    if gCanSend == True:
        if time.time() - lastSent > interval:
            print("Sending telemetry")
            payload = '{{"temp": {0},"du": {1}}}'
            iotc.sendTelemetry(payload.format(cpu.temperature, disk.usage))
            lastSent = time.time()
