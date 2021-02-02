import asyncio  # Needed for yielding to the event loop.
import xml.etree.ElementTree as ET

import hassapi as hass
import mqttapi as mqtt
import requests


class Foscam_C1(mqtt.Mqtt):
    async def initialize(self):
        self.log("Starting foscam c1")
        self.camsettings = self.args["camsettings"]
        self.camhost = self.camsettings["host"]
        self.portnr = str(self.camsettings["port"])
        self.user = self.camsettings["user"]
        self.password = self.camsettings["password"]
        self.camera_name = self.camsettings["camera_name"]
        self.mqtt_topic = self.camsettings["mqtt_topic"]
        self.is_alarmed = False
        self.count_no_alarm = 0

        self.url = (
            "http://"
            + self.camhost
            + ":"
            + str(self.portnr)
            + "/cgi-bin/CGIProxy.fcgi?&usr="
            + self.user
            + "&pwd="
            + self.password
            + "&cmd="
        )

        self.alarmsettings = self.args["alarmsettings"]
        self.motion_sensor = self.alarmsettings["motion_sensor"]
        await self.run_in(self.hass_cb, 5)  # This call also need to be awaited.

    async def send_command(self, command):
        try:
            response = requests.get(self.url + command, timeout=10)
            data = ET.fromstring(response.content)
        except Exception:
            return ""

        if data[0].text == "0":
            return data
        elif data[0].text == "-1" and "setMotion" in command:
            tree = ET.parse("<result>0</result>")
            data = tree.getroot()
            return data
        else:
            return ""

    async def hass_cb(self, kwargs):
        i = 0
        while True:
            i += 1
            self.log(f"Run time {i}")
            await self.get_sensors()
            await asyncio.sleep(
                3
            )  # Time to yield in seconds. Use a shorter time if needed, i.e. 0.1.

    async def get_sensors(self):
        data = await self.send_command("getDevState")
        if data == "":
            return
        try:
            motion_alarm = data.find("motionDetectAlarm").text
            if motion_alarm == "0":
                motion_alarm_text = "Disabled"
            elif motion_alarm == "1":
                self.count_no_alarm += 1
                motion_alarm_text = "No Alarm"
                if self.count_no_alarm > 5:
                    self.is_alarmed = False
                    self.count_no_alarm = 0
            elif motion_alarm == "2":
                motion_alarm_text = "Alarm!"
                if self.is_alarmed == False:
                    self.mqtt_publish(self.mqtt_topic, "Alarm")
                    self.is_alarmed = True
                    self.count_no_alarm = 0
            # self.set_state(self.motion_sensor, state=motion_alarm_text)
            self.log(motion_alarm_text)
        except Exception as e:
            self.log(e)
