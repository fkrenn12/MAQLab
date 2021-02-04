# --------------------------------------------------------
from Devices.BKPrecision import E2831
from Extensions.shared import validate_topic
from Extensions.shared import validate_payload
import math
import datetime


# --------------------------------------------------------
class BK2831E(E2831.BK2831E):
    def __init__(self, _port, _baudrate=9600):
        super().__init__(_port, _baudrate)
        self.__comport = ""
        self.__inventarnumber = "0"
        self.__commands = ["vdc?", "idc?", "vac?", "iac?", "f?", "r?"]

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

        try:
            command = t["cmd"]
            value = p["payload_float"]
        except:
            try:
                client.publish(t["reply"], p["payload_command_error"])
            except:
                raise
            return

        try:

            if command == "volt:dc?" or command == "vdc?":
                self.set_mode_vdc_auto_range()
                self.measure()
                client.publish(t["reply"], self.volt_as_string)
                return
            elif command == "volt:ac?" or command == "vac?":
                self.set_mode_vac_auto_range()
                self.measure()
                client.publish(t["reply"], self.volt_as_string)
                return
            elif command == "curr:dc?" or command == "curr:dc:high?" or command == "idc?":
                self.set_mode_idc_range_20A()
                self.measure()
                client.publish(t["reply"], self.current_as_string)
                return
            elif command == "curr:ac?" or command == "curr:ac:high?" or command == "iac?":
                self.set_mode_iac_range_20A()
                self.measure()
                client.publish(t["reply"], self.current_as_string)
                return
            elif command == "curr:ac:low?":
                self.set_mode_iac_range_200mA()
                self.measure()
                client.publish(t["reply"], self.current_as_string)
                return
            elif command == "curr:dc:low?":
                self.set_mode_idc_range_200mA()
                self.measure()
                client.publish(t["reply"], self.current_as_string)
                return
            elif command == "freq?" or command == "f?":
                self.set_mode_frequency_auto_range()
                self.measure()
                client.publish(t["reply"], self.frequence_as_string)
                return
            elif command == "res?" or command == "r?":
                self.set_mode_resistance_auto_range()
                self.measure()
                client.publish(t["reply"], self.resistance_as_string)
                return
            elif command == "volt:rms?" or command == "vrms?":
                self.set_mode_vdc_auto_range()
                self.measure()
                vdc = self.volt
                self.set_mode_vac_auto_range()
                self.measure()
                vac = self.volt
                vrms = math.sqrt(math.pow(vac, 2) + math.pow(vdc, 2))
                client.publish(t["reply"], "{:.6f}".format(vrms) + " VRMS")
                return
            elif command == "curr:rms?" or command == "irms?":
                self.set_mode_idc_range_20A()
                self.measure()
                idc = self.current
                self.set_mode_iac_range_20A()
                self.measure()
                iac = self.current
                irms = math.sqrt(math.pow(iac, 2) + math.pow(idc, 2))
                client.publish(t["reply"], "{:.6f}".format(irms) + " ARMS")
                return
            elif command == "pow:dc?" or command == "p:dc?" or command == "power:dc?":
                self.set_mode_vdc_auto_range()
                self.measure()
                vdc = self.volt
                self.set_mode_idc_range_20A()
                self.measure()
                idc = self.current
                power = vdc * idc
                client.publish(t["reply"], "{:.6f}".format(power) + " WDC")
                return
            elif command == "pow:ac?" or command == "p:ac?" or command == "power:ac?":
                self.set_mode_vac_auto_range()
                self.measure()
                vac = self.volt
                self.set_mode_iac_range_20A()
                self.measure()
                iac = self.current
                power = vac * iac
                client.publish(t["reply"], "{:.6f}".format(power) + " WAC")
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
            raise Exception("Command invalid")

        except Exception as e:
            client.publish(t["reply"], p["payload_error"] + ":" + str(e))
            return
        finally:
            return

    def on_created(self, comport, inventarnumber):
        self.__comport = comport
        self.__inventarnumber = inventarnumber
        print(str(
            datetime.datetime.now()) + "  :" + self.devicetype + " " + self.model + " plugged into " + self.__comport + ", Accessnumber is: "
              + str(inventarnumber))

    def on_destroyed(self):
        print(str(datetime.datetime.now()) + "  :" + self.model + " removed from " + self.__comport)
        self.__comport = ""

    def execute(self):
        pass
