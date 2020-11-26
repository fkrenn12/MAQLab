# --------------------------------------------------------
from Devices.Delta import SM70AR24 as _SM70AR24
from Extensions.shared import validate_topic
from Extensions.shared import validate_payload


# --------------------------------------------------------
class SM70AR24(_SM70AR24.SM70AR24):

    def __init__(self, addr):
        super().__init__(addr)
        self.__addr = addr
        self.__inventarnumber = "0"

    def mqttmessage(self, client, msg):
        t = validate_topic(msg.topic, self.__inventarnumber, self.model)
        p = validate_payload(msg.payload)

        if not t["valid"]:
            return

        if not p["valid"]:
            client.publish(t["reply"], p["payload_error"])
            return

        if t["cmd"] == "accessnumber":
            client.publish(t["reply"], str(self.__inventarnumber))
            return

        if not t["matching"]:
            return

        print(self.model + " " + t["topic"] + " " + str(p["payload"]))

        command = t["cmd"]
        value = p["payload"]

    def on_created(self, addr, inventarnumber):
        self.__addr = addr
        self.__inventarnumber = inventarnumber
        print(self.devicetype + " " + self.model + " plugged into " + str(self.__addr) + ", Inventory number is: "
              + str(inventarnumber))

    def on_destroyed(self):
        print(self.model + " removed from " + str(self.__addr))
        self.__addr = ("0", 0)

    def execute(self):
        pass
