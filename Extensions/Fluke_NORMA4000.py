# --------------------------------------------------------
from Devices.Fluke import NORMA4000 as _NORMA4000
from Extensions.shared import validate_topic
from Extensions.shared import validate_payload

import datetime


# --------------------------------------------------------
class NORMA4000(_NORMA4000.NORMA4000):

    def __init__(self, addr):
        super().__init__(addr)
        self.__addr = addr
        self.__inventarnumber = "0"
        self.__commands = ["vdc?", "idc?", "vdc", "idc"]

    def mqttmessage(self, client, msg):
        try:
            t = validate_topic(msg.topic, self.__inventarnumber, self.model)
        except:
            # we cannot handle the topic which made an exception
            return

        try:
            p = validate_payload(msg.payload)
        except:
            client.publish(t["reply"], p["payload_error"])
            return

        if t["cmd"] == "accessnumber":
            client.publish(t["reply"], str(self.__inventarnumber))
            return

        if not t["matching"]:
            return

        print(self.model + " " + t["topic"] + " " + str(p["payload"]))

        command = t["cmd"]
        value = p["payload_float"]

    def on_created(self, addr, inventarnumber):
        self.__addr = addr
        self.__inventarnumber = inventarnumber
        print(str(datetime.datetime.now()) + "  :" + self.devicetype + " " + self.model + " plugged into " + str(
            self.__addr) + ", Accessnumber is: "
              + str(inventarnumber))

    def on_destroyed(self):
        print(str(datetime.datetime.now()) + "  :" + self.model + " removed from " + str(self.__addr))
        self.__addr = ("0", 0)

    def __get_accessnumber(self):
        return  self.__inventarnumber

    def execute(self):
        pass

    accessnumber = property(__get_accessnumber)
