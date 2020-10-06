# --------------------------------------------------------
from Devices.Manson import NTP6531 as _NTP6531

import time
import threading
import global_share as g
import datetime


class NTP6531(_NTP6531.NTP6531):

    def __init__(self, _port, _baudrate=9600):
        super().__init__(_port, _baudrate)
        self.__client = None

    def mqttmessage(self, client, msg):
        timestamp = str(datetime.datetime.utcnow())
        self.__client = client
        print(msg.topic, msg.payload)
        topic_in = msg.topic.lower()
        topic_in_split = topic_in.split("/")
        # immediately prepare topic for reply at the end of this code section
        topic_out = topic_in.replace(g.topic_cmd, g.topic_reply)
        payload_in = msg.payload.lower()
        payload_out = "error: " + timestamp
        if topic_in_split[1] == g.topic_cmd:
            # parsing the topic
            if topic_in_split[2] == g.topic_request:
                # reply the ? request
                client.publish(g.topic_root + "/" + g.topic_reply + "/" + self.model + "/sernum",
                               str(self.serialnumber))
                return

            elif topic_in_split[2] != str(self.serialnumber):
                # serialnumber does not match, so we exit doing nothing
                # because an other device could handle this message
                return
            else:
                # the serial numbers are matching
                # check and prepare the payload
                if isinstance(payload_in, bytes):
                    # we do not handle empty payload
                    if payload_in == b'':
                        client.publish(topic_out, payload_out)
                        return
                    # convert it to str
                    payload_in = payload_in.decode("utf-8")
                else:
                    # payload which is not bytes cannot be correct
                    client.publish(topic_out, payload_out)
                    return

                # transpose "off" and "on"
                payload_in = payload_in.replace('off', "0")
                payload_in = payload_in.replace("on", "1")
                try:
                    value = float(payload_in)
                except:
                    # if value cannot be cast into float
                    # we reply error and exit
                    value = 0
                    client.publish(topic_out, payload_out)
                    return

                accepted = False
                if "output" in topic_in_split[3]:
                    if int(value) == 0:
                        self.output_off()
                        accepted = True
                    else:
                        self.output_on()
                        accepted = True

                elif "apply" in topic_in_split[3]:
                    if "volt" in topic_in_split[4]:
                        # checking the value limits
                        if _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT >= value >= _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT:
                            self.apply_volt = value
                            accepted = True
                    elif "curr" in topic_in_split[4]:
                        # checking limits
                        if _NTP6531.NTP6531_CURRENT_HIGH_LIMIT >= value >= _NTP6531.NTP6531_CURRENT_LOW_LIMIT:
                            self.apply_current = value
                            accepted = True

                if accepted:
                    payload_out = "accepted: " + timestamp

                client.publish(topic_out, payload_out)

    def on_created(self):
        print("NTP6531Ser:" + str(self.serialnumber) + " plugged in")

    def on_destroyed(self):
        print("NTP6531 removed")

    def execute(self):

        pass
