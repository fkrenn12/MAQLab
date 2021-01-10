# --------------------------------------------------------
from Devices.Keithley import SM2400 as _SM2400
from Extensions.shared import validate_topic
from Extensions.shared import validate_payload
import datetime


# --------------------------------------------------------
class SM2400(_SM2400.SM2400):

    def __init__(self, _port, _baudrate=9600):
        super().__init__(_port, _baudrate)
        self.__comport = ""
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
        if command == "volt:dc?" or command == "volt?" or command == "vdc?":
            self.set_mode_volt_meter()
            self.measure()
            client.publish(t["reply"], self.volt_as_string)
            return
        elif command == "curr:dc?" or command == "curr?" or command == "idc?":
            self.set_mode_ampere_meter()
            self.measure()
            client.publish(t["reply"], self.current_as_string)
            return
        elif command == "res?" or command == "r?" or command == "res2?" or command == "r2?":
            self.set_mode_ohmmeter_2wire()
            self.measure()
            client.publish(t["reply"], self.resistance_as_string)
            return
        elif command == "res4?" or command == "r4?":
            self.set_mode_ohmmeter_4wire()
            self.measure()
            client.publish(t["reply"], self.resistance_as_string)
            return
        elif command == "?":
            client.publish(t["reply"] + "/manufactorer", self.manufactorer)
            client.publish(t["reply"] + "/devicetype", self.devicetype)
            client.publish(t["reply"] + "/model", self.model)
            client.publish(t["reply"] + "/serialnumber", str(self.serialnumber))
            return
        elif command == "echo?" or command == "ping?":
            client.publish(t["reply"], str(datetime.datetime.utcnow()))
            return
        return


    def on_created(self, comport, inventarnumber):
        self.__comport = comport
        self.__inventarnumber = inventarnumber
        print(str(
            datetime.datetime.now()) + "  :" + self.devicetype + " " + self.model + " plugged into " + self.__comport + ", Inventory number is: "
              + str(inventarnumber))

    def on_destroyed(self):
        print(str(datetime.datetime.now()) + "  :" + self.model + " removed from " + self.__comport)
        self.__comport = ""

    def execute(self):
        pass
