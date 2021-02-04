import datetime
from numpy import clip
# --------------------------------------------------------
from Devices.Manson import NTP6531 as _NTP6531
from Extensions.shared import validate_topic
from Extensions.shared import validate_payload


class NTP6531(_NTP6531.NTP6531):

    def __init__(self, _port, _baudrate=9600):
        super().__init__(_port, _baudrate)
        self.__comport = ""
        self.__invent_number = "0"
        self.__commands = ["vdc?", "idc?", "vdc", "idc", "output"]

    def mqttmessage(self, client, msg):

        try:
            t = validate_topic(msg.topic, self.__invent_number, self.model)
        except:
            # we cannot handle the topic which made an exception
            return

        try:
            p = validate_payload(msg.payload)
        except:
            client.publish(t["reply"], p["payload_error"])
            return

        if t["cmd"] == "accessnumber":
            client.publish(t["reply"], str(self.__invent_number))
            return

        if not t["matching"]:
            return

        # print(self.model + " " + t["topic"] + " " + str(p["payload"]))

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
            if command == "output":
                if int(value) == 0:
                    self.output_off()
                    client.publish(t["reply"], p["payload_accepted"])
                else:
                    self.output_on()
                    client.publish(t["reply"], p["payload_accepted"])
                return
            # ------------------------------------------------------------------------------------------------
            # V O L T A G E commands - Handling
            # ------------------------------------------------------------------------------------------------
            elif command == "volt?" or command == "volt:dc?" or command == "vdc?":
                client.publish(t["reply"], self.volt_as_string)
                return
            elif command == "volt_applied?" or command == "applied:volt:dc?" or command == "applied_vdc?":
                client.publish(t["reply"], str(self.apply_volt) + " VDC")
                return
            elif command == "volt" or command == "volt:dc" or command == "vdc":
                # checking the value limits
                if _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT >= value >= _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT:
                    self.apply_volt = value
                    client.publish(t["reply"], p["payload_accepted"])
                    return
            elif command == "volt_max?" or command == "volt:max?" or command == "vmax?":
                client.publish(t["reply"], str(_NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT) + " VDC")
                return
            elif command == "volt_min?" or command == "volt:min?" or command == "vmin?":
                client.publish(t["reply"], str(_NTP6531.NTP6531_VOLTAGE_LOW_LIMIT) + " VDC")
                return
            elif command == "volt_limit_up?" or command == "volt:limit:up?" or command == "vup?":
                client.publish(t["reply"], str(self.volt_limit_upper) + " VDC")
                return
            elif command == "volt_limit_up" or command == "volt:limit:up" or command == "vup":
                # checking limits
                if _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT >= value >= _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT:
                    self.volt_limit_upper = value
                    client.publish(t["reply"], p["payload_accepted"])
                    return
            elif command == "volt_limit_low?" or command == "volt:limit:low?" or command == "vlow?":
                client.publish(t["reply"], str(self.volt_limit_lower) + " VDC")
                return
            elif command == "volt_limit_low" or command == "volt:limit:low" or command == "vlow":
                # checking limits
                if _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT >= value >= _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT:
                    self.volt_limit_lower = value
                    client.publish(t["reply"], p["payload_accepted"])
                    return
            # ------------------------------------------------------------------------------------------------
            # C U R R E N T commands - Handling
            # ------------------------------------------------------------------------------------------------
            elif command == "curr" or command == "curr:dc" or command == "idc":
                # checking limits
                if _NTP6531.NTP6531_CURRENT_HIGH_LIMIT >= value >= _NTP6531.NTP6531_CURRENT_LOW_LIMIT:
                    self.apply_current = value
                    client.publish(t["reply"], p["payload_accepted"])
                    return
            elif command == "curr_applied?" or command == "applied:curr:dc?" or command == "applied_idc?":
                client.publish(t["reply"], str(self.apply_current) + " ADC")
                return
            elif command == "curr?" or command == "curr:dc?" or command == "idc?":
                client.publish(t["reply"], self.current_as_string)
                return
            elif command == "curr_max?" or command == "curr:max?" or command == "imax?":
                client.publish(t["reply"], str(_NTP6531.NTP6531_CURRENT_HIGH_LIMIT) + " ADC")
                return
            elif command == "curr_min?" or command == "curr:min?" or command == "imin?":
                client.publish(t["reply"], str(_NTP6531.NTP6531_CURRENT_LOW_LIMIT) + " ADC")
                return
            elif command == "curr_limit_up?" or command == "curr:limit:up?" or command == "iup?":
                client.publish(t["reply"], str(self.current_limit_upper) + " ADC")
                return
            elif command == "curr_limit_up" or command == "curr:limit:up" or command == "iup":
                # checking limits
                if _NTP6531.NTP6531_CURRENT_HIGH_LIMIT >= value >= _NTP6531.NTP6531_CURRENT_LOW_LIMIT:
                    self.current_limit_upper = value
                    client.publish(t["reply"], p["payload_accepted"])
                    return
            elif command == "curr_limit_low?" or command == "curr:limit:low?" or command == "ilow?":
                client.publish(t["reply"], str(self.current_limit_lower) + " ADC")
                return
            elif command == "curr_limit_low" or command == "curr:limit:low" or command == "ilow":
                # checking limits
                if _NTP6531.NTP6531_CURRENT_HIGH_LIMIT >= value >= _NTP6531.NTP6531_CURRENT_LOW_LIMIT:
                    self.current_limit_lower = value
                    client.publish(t["reply"], p["payload_accepted"])
                    return
            # ------------------------------------------------------------------------------------------------
            # O T H E R commands - Handling
            # ------------------------------------------------------------------------------------------------
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
            pass

    def on_created(self, comport, invent_number):
        self.__comport = comport
        self.__invent_number = invent_number
        print(str(datetime.datetime.now()) + "  :" + self.devicetype + " " + self.model + " plugged into " + self.__comport + ", Accessnumber is: "
              + str(invent_number))

    def on_destroyed(self):
        print(str(datetime.datetime.now()) + "  :" + self.model + " removed from " + self.__comport)
        self.__comport = ""

    def execute(self):
        pass
