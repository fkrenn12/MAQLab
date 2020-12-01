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
        if command == "output":
            if int(value) == 0:
                self.output_off()
                client.publish(t["reply"], p["payload_accepted"])
            else:
                self.output_on()
                client.publish(t["reply"], p["payload_accepted"])
            return
        elif command == "volt" or command == "volt:dc" or command == "vdc":
            # checking the value limits
            if _SM70AR24.SM70AR24_VOLTAGE_HIGH_LIMIT >= value >= _SM70AR24.SM70AR24_VOLTAGE_LOW_LIMIT:
                self.apply_volt = value
                client.publish(t["reply"], p["payload_accepted"])
                return
        elif command == "curr" or command == "curr:dc" or command == "idc":
            # checking limits
            if _SM70AR24.SM70AR24_CURRENT_HIGH_LIMIT >= value >= _SM70AR24.SM70AR24_CURRENT_LOW_LIMIT:
                self.apply_current = value
                client.publish(t["reply"], p["payload_accepted"])
                return
        elif command == "volt?" or command == "volt:dc?" or command == "vdc?":
            # TODO
            # client.publish(t["reply"], self.volt_as_string)
            return
        elif command == "curr?" or command == "curr:dc?" or command == "idc?":
            # TODO
            # client.publish(t["reply"], self.current_as_string)
            return
        elif command == "power?" or command == "pow?" or command == "p?":
            # TODO
            # volt = self.volt
            # curr = self.current
            # power = volt * curr
            # client.publish(t["reply"], "{:.6f}".format(power) + " WDC")
            return
        elif command == "mode?":
            # TODO
            # client.publish(t["reply"], self.source_mode)
            return
        elif command == "volt_max?" or command == "volt:upper?" or command == "vmax?":
            client.publish(t["reply"], str(_SM70AR24.SM70AR24_VOLTAGE_HIGH_LIMIT) + " VDC")
            return
        elif command == "volt_min?" or command == "volt:lower?" or command == "vmin?":
            client.publish(t["reply"], str(_SM70AR24.SM70AR24_VOLTAGE_LOW_LIMIT) + " VDC")
            return
        elif command == "curr_max?" or command == "curr:upper?" or command == "imax?":
            client.publish(t["reply"], str(_SM70AR24.SM70AR24_CURRENT_HIGH_LIMIT) + " ADC")
            return
        elif command == "curr_min?" or command == "curr:lower?" or command == "imin?":
            client.publish(t["reply"], str(_SM70AR24.SM70AR24_CURRENT_LOW_LIMIT) + " ADC")
            return
        elif command == "?":
            client.publish(t["reply"] + "/manufactorer", self.manufactorer)
            client.publish(t["reply"] + "/devicetype", self.devicetype)
            client.publish(t["reply"] + "/model", self.model)
            client.publish(t["reply"] + "/serialnumber", str(self.serialnumber))
            return

        client.publish(t["reply"], p["payload_error"])

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