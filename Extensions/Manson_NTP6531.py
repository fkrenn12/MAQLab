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
        self.__comport = ""
        self.__inventarnumber = "0"

    def mqttmessage(self, client, msg):
        timestamp = str(datetime.datetime.utcnow())
        self.__client = client

        topic_received = msg.topic.lower()
        topic_received_split = topic_received.split("/")
        # check the number of elements in splitted topic
        # we want to avoid exception because of list overflows
        # when there are received topics with false syntax and format
        # TODO: ---------- USERID berücksichtigen
        numsplits = len(topic_received_split)
        if numsplits < 3 or numsplits > 4:
            return
        # TODO: ---------- USERID berücksichtigen
        # immediately prepare topic for reply at the end of this code section
        topic_reply = topic_received.replace(g.topic_cmd, g.topic_reply)
        payload_received = msg.payload.lower()
        if isinstance(payload_received, bytes):
            payload_received = payload_received.decode("utf-8")
        if not isinstance(payload_received, str):
            payload_received = str(payload_received)
        payload_error = "error: " + timestamp
        payload_accepted = "accepted: " + timestamp
        if topic_received_split[1] == g.topic_cmd:
            # parsing the topic
            if topic_received_split[2] == g.topic_request:
                # reply the ? request
                client.publish(g.topic_root + "/" + g.topic_reply + "/" + self.model + "/accessnumber",
                               str(self.__inventarnumber))
                return

            elif topic_received_split[2] != str(self.serialnumber):
                # serialnumber does not match, so we exit doing nothing
                # because an other device could handle this message
                return
            else:
                print("NTP-6531 " + str(msg.topic) + " " + str(msg.payload))
                # the serial numbers are matching
                # transpose "off" and "on"
                payload_received = payload_received.replace('off', "0")
                payload_received = payload_received.replace("on", "1")
                try:
                    value = float(payload_received)
                except:
                    # if value cannot be cast into float
                    # we reply error and exit
                    client.publish(topic_reply, payload_error)
                    return
                command = topic_received_split[3]
                command = command.replace("1", "")
                command = command.replace(" ", "")
                if command == "output":
                    if int(value) == 0:
                        self.output_off()
                        client.publish(topic_reply, payload_accepted)
                        return
                    else:
                        self.output_on()
                        client.publish(topic_reply, payload_accepted)
                        return
                elif command == "volt" or command == "volt:dc" or command == "vdc":
                    # checking the value limits
                    if _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT >= value >= _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT:
                        self.apply_volt = value
                        client.publish(topic_reply, payload_accepted)
                        return
                elif command == "curr" or command == "curr:dc" or command == "idc":
                    # checking limits
                    if _NTP6531.NTP6531_CURRENT_HIGH_LIMIT >= value >= _NTP6531.NTP6531_CURRENT_LOW_LIMIT:
                        self.apply_current = value
                        client.publish(topic_reply, payload_accepted)
                        return
                elif command == "volt?" or command == "volt:dc?" or command == "vdc?":
                    client.publish(topic_reply, self.volt_as_string)
                    return
                elif command == "curr?" or command == "curr:dc?" or command == "idc?":
                    client.publish(topic_reply, self.current_as_string)
                    return
                elif command == "power?" or command == "pow?" or command == "p?":
                    volt = self.volt
                    curr = self.current
                    power = volt * curr
                    client.publish(topic_reply, "{:.6f}".format(power) + " WDC")
                    return
                elif command == "mode?":
                    client.publish(topic_reply, self.source_mode)
                    return

                client.publish(topic_reply, payload_error)

    def on_created(self, comport, inventarnumber):
        self.__comport = comport
        self.__inventarnumber = inventarnumber
        print(self.devicetype + " " + self.model + " Inventarnumber: "
              + str(inventarnumber) + " plugged into " + self.__comport)

    def on_destroyed(self):
        print(self.model + " removed from " + self.__comport)
        self.__comport = ""

    def execute(self):

        pass
