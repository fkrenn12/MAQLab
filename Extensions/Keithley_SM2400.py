# --------------------------------------------------------
from Devices.Keithley import SM2400 as _SM2400
import global_share as g
import datetime
import math


# --------------------------------------------------------
class SM2400(_SM2400.SM2400):

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
            elif topic_received_split[2] != str(self.__inventarnumber):
                # serialnumber does not match, so we exit doing nothing
                # and let other device handle this message
                return
            else:
                # the serial numbers are matching
                print("SM2400 " + str(msg.topic) + " " + str(msg.payload))
                command = topic_received_split[3]
                command = command.replace("1", "")
                command = command.replace(" ", "")
                if command == "volt:dc?" or command == "volt?" or command == "vdc?":
                    self.set_mode_volt_meter()
                    self.measure()
                    client.publish(topic_reply, self.volt_as_string)
                    return
                elif command == "curr:dc?" or command == "curr?" or command == "idc?":
                    self.set_mode_ampere_meter()
                    self.measure()
                    client.publish(topic_reply, self.current_as_string)
                    return
                elif command == "res?" or command == "r?" or command == "res2?" or command == "r2?":
                    self.set_mode_ohmmeter_2wire()
                    self.measure()
                    client.publish(topic_reply, self.resistance_as_string)
                    return
                elif command == "res4?" or command == "r4?":
                    self.set_mode_ohmmeter_4wire()
                    self.measure()
                    client.publish(topic_reply, self.resistance_as_string)
                    return
                elif command == "?":
                    client.publish(topic_reply + "/manufactorer", self.manufactorer)
                    client.publish(topic_reply + "/devicetype", self.devicetype)
                    client.publish(topic_reply + "/model", self.model)
                    client.publish(topic_reply + "/serialnumber", str(self.serialnumber))
                    return
                return

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
