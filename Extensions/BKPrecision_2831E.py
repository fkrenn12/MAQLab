# --------------------------------------------------------
from Devices.BKPrecision import E2831
import datetime
import global_share as g
import math


# --------------------------------------------------------
class BK2831E(E2831.BK2831E):
    def __init__(self, _port, _baudrate=9600):
        super().__init__(_port, _baudrate)
        self.__client = None
        self.__comport = ""
        self.__inventarnumber = "0"

    def mqttmessage(self, client, msg):
        timestamp = str(datetime.datetime.utcnow())
        self.__client = client
        print("BKPrecision")
        print(msg.topic, msg.payload)
        topic_received = msg.topic.lower()
        topic_received_split = topic_received.split("/")
        # check the number of elements in splitted topic
        # we want to avoid exception because of list overflows
        # when there are received topics with false syntax and format

        numsplits = len(topic_received_split)
        if numsplits < 3 or numsplits > 4:
            return

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
                # because an other device could handle this message
                return
            else:
                # the serial numbers are matching
                command = topic_received_split[3]
                command = command.replace("1", "")
                command = command.replace(" ", "")
                if command == "volt:dc?" or command == "vdc?":
                    self.set_mode_vdc_auto_range()
                    self.measure()
                    client.publish(topic_reply, self.volt_as_string)
                    return
                elif command == "volt:ac?" or command == "vac?":
                    self.set_mode_vac_auto_range()
                    self.measure()
                    client.publish(topic_reply, self.volt_as_string)
                    return
                elif command == "curr:dc?" or command == "curr:dc:high?" or command == "idc?":
                    self.set_mode_idc_range_20A()
                    self.measure()
                    client.publish(topic_reply, self.current_as_string)
                    return
                elif command == "curr:ac?" or command == "curr:ac:high?" or command == "iac?":
                    self.set_mode_iac_range_20A()
                    self.measure()
                    client.publish(topic_reply, self.current_as_string)
                elif command == "curr:ac:low?":
                    self.set_mode_iac_range_200mA()
                    self.measure()
                    client.publish(topic_reply, self.current_as_string)
                elif command == "curr:dc:low?":
                    self.set_mode_idc_range_200mA()
                    self.measure()
                    client.publish(topic_reply, self.current_as_string)
                elif command == "freq?" or command == "f?":
                    self.set_mode_frequency_auto_range()
                    self.measure()
                    client.publish(topic_reply, self.frequence_as_string)
                elif command == "res?" or command == "r?":
                    self.set_mode_resistance_auto_range()
                    self.measure()
                    client.publish(topic_reply, self.resistance_as_string)
                elif command == "volt:rms?" or command == "vrms?":
                    self.set_mode_vdc_auto_range()
                    self.measure()
                    vdc = self.volt
                    self.set_mode_vac_auto_range()
                    self.measure()
                    vac = self.volt
                    vrms = math.sqrt(math.pow(vac, 2) + math.pow(vdc, 2))
                    client.publish(topic_reply, "{:.6f}".format(vrms) + " VRMS")
                elif command == "curr:rms?" or command == "irms?":
                    self.set_mode_idc_range_20A()
                    self.measure()
                    idc = self.current
                    self.set_mode_iac_range_20A()
                    self.measure()
                    iac = self.current
                    irms = math.sqrt(math.pow(iac, 2) + math.pow(idc, 2))
                    client.publish(topic_reply, "{:.6f}".format(irms) + " ARMS")
                elif command == "pow:dc?" or command == "p:dc?" or command == "power:dc?":
                    self.set_mode_vdc_auto_range()
                    self.measure()
                    vdc = self.volt
                    self.set_mode_idc_range_20A()
                    self.measure()
                    idc = self.current
                    power = vdc * idc
                    client.publish(topic_reply, "{:.6f}".format(power) + " WDC")
                elif command == "pow:ac?" or command == "p:ac?" or command == "power:ac?":
                    self.set_mode_vac_auto_range()
                    self.measure()
                    vac = self.volt
                    self.set_mode_iac_range_20A()
                    self.measure()
                    iac = self.current
                    power = vac * iac
                    client.publish(topic_reply, "{:.6f}".format(power) + " WAC")
                elif command == "?":
                    client.publish(topic_reply + "/manufactorer", self.manufactorer)
                    client.publish(topic_reply + "/devicetype", self.devicetype)
                    client.publish(topic_reply + "/model", self.model)
                    client.publish(topic_reply + "/serialnumber", str(self.serialnumber))

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
