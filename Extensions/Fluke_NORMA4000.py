# --------------------------------------------------------
import Extensions
from Devices.Fluke import NORMA4000 as _NORMA4000
import time


class NORMA4000(_NORMA4000.NORMA4000, Extensions.Device):

    def __init__(self, addr):
        _NORMA4000.NORMA4000.__init__(self, addr)
        Extensions.Device.__init__(self)
        self.__commands = ["vdc?", "idc?", "vdc", "idc"]

    def run(self) -> None:
        while True:
            time.sleep(1)
            print("Running" + str(self.accessnumber))

    def mqttmessage(self, client, msg):
        try:
            t = self.validate_topic(msg.topic, self.accessnumber, self.model)
        except:
            # we cannot handle the topic which made an exception
            return

        try:
            p = self.validate_payload(msg.payload)
        except:
            client.publish(t["reply"], p["payload_error"])
            return

        if t["cmd"] == "accessnumber":
            client.publish(t["reply"], str(self.accessnumber))
            return

        if not t["matching"]:
            return

        print(self.model + " " + t["topic"] + " " + str(p["payload"]))

        command = t["cmd"]
        value = p["payload_float"]
