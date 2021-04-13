# --------------------------------------------------------
from Devices.Keithley import SM2400 as _SM2400
import Extensions
import time
import datetime


class SM2400(_SM2400.SM2400, Extensions.Device):

    def __init__(self, _port, _baudrate=9600):
        _SM2400.SM2400.__init__(self, _port, _baudrate)
        Extensions.Device.__init__(self)
        self.__commands = ["vdc?", "idc?"]  # TODO: noch nicht komplett

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
            client.publish(t["reply"] + "/commands", str(self.__commands))
            return
        elif command == "echo?" or command == "ping?":
            client.publish(t["reply"], str(datetime.datetime.utcnow()))
            return
        return
