# --------------------------------------------------------
from Devices.Delta import SM70AR24 as _SM70AR24
from Extensions.shared import validate_topic
from Extensions.shared import validate_payload
import datetime
import Extensions


# --------------------------------------------------------
#class SM70AR24(_SM70AR24.SM70AR24):

    #def __init__(self, addr):
    #    super().__init__(addr)
class SM70AR24(_SM70AR24.SM70AR24, Extensions.Device):

    def __init__(self, addr):
        _SM70AR24.SM70AR24.__init__(self, addr)
        Extensions.Device.__init__(self)
        self.__addr = addr
        self.__inventarnumber = "0"
        self.__commands = ["vdc?", "idc?", "vdc", "idc", "output"]

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
                if _SM70AR24.SM70AR24_VOLTAGE_HIGH_LIMIT >= value >= _SM70AR24.SM70AR24_VOLTAGE_LOW_LIMIT:
                    self.apply_volt = value
                    client.publish(t["reply"], p["payload_accepted"])
                    return
            elif command == "volt_max?" or command == "volt:max?" or command == "vmax?":
                client.publish(t["reply"], str(_SM70AR24.SM70AR24_VOLTAGE_HIGH_LIMIT) + " VDC")
                return
            elif command == "volt_min?" or command == "volt:min?" or command == "vmin?":
                client.publish(t["reply"], str(_SM70AR24.SM70AR24_VOLTAGE_LOW_LIMIT) + " VDC")
                return
            elif command == "volt_limit_up?" or command == "volt:limit:up?" or command == "vup?":
                client.publish(t["reply"], str(self.volt_limit_upper) + " VDC")
                return
            elif command == "volt_limit_up" or command == "volt:limit:up" or command == "vup":
                # checking limits
                if _SM70AR24.SM70AR24_VOLTAGE_HIGH_LIMIT >= value >= _SM70AR24.SM70AR24_VOLTAGE_LOW_LIMIT:
                    self.volt_limit_upper = value
                    client.publish(t["reply"], p["payload_accepted"])
                    return
            elif command == "volt_limit_low?" or command == "volt:limit:low?" or command == "vlow?":
                client.publish(t["reply"], str(self.volt_limit_lower) + " VDC")
                return
            elif command == "volt_limit_low" or command == "volt:limit:low" or command == "vlow":
                # checking limits
                if _SM70AR24.SM70AR24_VOLTAGE_HIGH_LIMIT >= value >= _SM70AR24.SM70AR24_VOLTAGE_LOW_LIMIT:
                    self.volt_limit_lower = value
                    client.publish(t["reply"], p["payload_accepted"])
                    return
            # ------------------------------------------------------------------------------------------------
            # C U R R E N T commands - Handling
            # ------------------------------------------------------------------------------------------------
            elif command == "curr" or command == "curr:dc" or command == "idc":
                # checking limits
                if _SM70AR24.SM70AR24_CURRENT_HIGH_LIMIT >= value >= _SM70AR24.SM70AR24_CURRENT_LOW_LIMIT:
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
                client.publish(t["reply"], str(_SM70AR24.SM70AR24_CURRENT_HIGH_LIMIT) + " ADC")
                return
            elif command == "curr_min?" or command == "curr:min?" or command == "imin?":
                client.publish(t["reply"], str(_SM70AR24.SM70AR24_CURRENT_LOW_LIMIT) + " ADC")
                return
            elif command == "curr_limit_up?" or command == "curr:limit:up?" or command == "iup?":
                client.publish(t["reply"], str(self.current_limit_upper) + " ADC")
                return
            elif command == "curr_limit_up" or command == "curr:limit:up" or command == "iup":
                # checking limits
                if _SM70AR24.SM70AR24_CURRENT_HIGH_LIMIT >= value >= _SM70AR24.SM70AR24_CURRENT_LOW_LIMIT:
                    self.current_limit_upper = value
                    client.publish(t["reply"], p["payload_accepted"])
                    return
            elif command == "curr_limit_low?" or command == "curr:limit:low?" or command == "ilow?":
                client.publish(t["reply"], str(self.current_limit_lower) + " ADC")
                return
            elif command == "curr_limit_low" or command == "curr:limit:low" or command == "ilow":
                # checking limits
                if _SM70AR24.SM70AR24_CURRENT_HIGH_LIMIT >= value >= _SM70AR24.SM70AR24_CURRENT_LOW_LIMIT:
                    self.current_limit_lower = value
                    client.publish(t["reply"], p["payload_accepted"])
                    return
            # ------------------------------------------------------------------------------------------------
            elif command == "power?" or command == "pow?" or command == "p?":
                volt = self.volt
                curr = self.current
                power = volt * curr
                client.publish(t["reply"], "{:.6f}".format(power) + " WDC")
                return
            # ------------------------------------------------------------------------------------------------
            elif command == "mode?":
                # TODO
                # client.publish(t["reply"], self.source_mode)
                return
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

    '''
    def on_created(self, addr, inventarnumber):
        self.__addr = addr
        self.__inventarnumber = inventarnumber
        print(str(datetime.datetime.now()) + "  :" + self.devicetype + " " + self.model + " plugged into " + str(
            self.__addr) + ", Accessnumber is: "
              + str(inventarnumber))

    def on_destroyed(self):
        print(str(datetime.datetime.now()) + "  :" + self.model + " removed from " + str(self.__addr))
        self.__addr = ("0", 0)
    '''

    def __get_accessnumber(self):
        return self.__inventarnumber

    def execute(self):
        pass

    accessnumber = property(__get_accessnumber)