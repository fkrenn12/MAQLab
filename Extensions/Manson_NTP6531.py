import datetime
import threading
import time
import Extensions
from External_modules.subpub import SubPub
from numpy import clip
# --------------------------------------------------------
from Devices.Manson import NTP6531 as _NTP6531


class NTP6531(_NTP6531.NTP6531, Extensions.Device):

    def __init__(self, _port, _baudrate=9600):
        _NTP6531.NTP6531.__init__(self, _port, _baudrate)
        Extensions.Device.__init__(self)
        self.__commands = ["vdc?", "idc?", "vdc", "idc", "output"]
        self.stop = False

    def run(self) -> None:
        while True:
            time.sleep(0.025)
            if self.stop:
                break
            try:
                match, data = self.mqtt.get(block=False)
            except:
                continue

            topic = match.string
            payload = data

            try:
                t = self.validate_topic(topic, self.accessnumber, self.model)
            except:
                # we cannot handle the topic which made an exception
                continue
                
            reply_topic = str(t["reply"])
            
            try:
                p = self.validate_payload(payload)
            except:
                self.sp.publish(reply_topic, str(p["payload_error"]))
                continue

            payload_accepted = p["payload_accepted"]
            
            if t["cmd"] == "accessnumber":
                self.sp.publish(reply_topic, str(self.accessnumber))
                continue

            if not t["matching"]:
                continue

            # print(self.model + " " + t["topic"] + " " + str(p["payload"]))

            try:
                command = t["cmd"]
                value = p["payload_float"]
            except:
                try:
                    self.sp.publish(reply_topic, str(p["payload_command_error"]))
                except:
                    raise
                continue

            try:
                if command == "output":
                    if int(value) == 0:
                        self.output_off()
                        self.sp.publish(reply_topic, payload_accepted)
                    else:
                        self.output_on()
                        self.sp.publish(reply_topic, payload_accepted)
                    continue
                # ------------------------------------------------------------------------------------------------
                # V O L T A G E commands - Handling
                # ------------------------------------------------------------------------------------------------
                elif command == "volt?" or command == "volt:dc?" or command == "vdc?":
                    self.sp.publish(reply_topic, self.volt_as_string)
                    continue
                elif command == "volt_applied?" or command == "applied:volt:dc?" or command == "applied_vdc?":
                    self.sp.publish(reply_topic, str(self.apply_volt) + " VDC")
                    continue
                elif command == "volt" or command == "volt:dc" or command == "vdc":
                    # checking the value limits
                    if _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT >= value >= _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT:
                        self.apply_volt = value
                        self.sp.publish(reply_topic, payload_accepted)
                        continue
                elif command == "volt_max?" or command == "volt:max?" or command == "vmax?":
                    self.sp.publish(reply_topic, str(_NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT) + " VDC")
                    continue
                elif command == "volt_min?" or command == "volt:min?" or command == "vmin?":
                    self.sp.publish(reply_topic, str(_NTP6531.NTP6531_VOLTAGE_LOW_LIMIT) + " VDC")
                    continue
                elif command == "volt_limit_up?" or command == "volt:limit:up?" or command == "vup?":
                    self.sp.publish(reply_topic, str(self.volt_limit_upper) + " VDC")
                    continue
                elif command == "volt_limit_up" or command == "volt:limit:up" or command == "vup":
                    # checking limits
                    if _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT >= value >= _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT:
                        self.volt_limit_upper = value
                        self.sp.publish(reply_topic, payload_accepted)
                        continue
                elif command == "volt_limit_low?" or command == "volt:limit:low?" or command == "vlow?":
                    self.sp.publish(reply_topic, str(self.volt_limit_lower) + " VDC")
                    continue
                elif command == "volt_limit_low" or command == "volt:limit:low" or command == "vlow":
                    # checking limits
                    if _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT >= value >= _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT:
                        self.volt_limit_lower = value
                        self.sp.publish(reply_topic, payload_accepted)
                        continue
                # ------------------------------------------------------------------------------------------------
                # C U R R E N T commands - Handling
                # ------------------------------------------------------------------------------------------------
                elif command == "curr" or command == "curr:dc" or command == "idc":
                    # checking limits
                    if _NTP6531.NTP6531_CURRENT_HIGH_LIMIT >= value >= _NTP6531.NTP6531_CURRENT_LOW_LIMIT:
                        self.apply_current = value
                        self.sp.publish(reply_topic, payload_accepted)
                        continue
                elif command == "curr_applied?" or command == "applied:curr:dc?" or command == "applied_idc?":
                    self.sp.publish(reply_topic, str(self.apply_current) + " ADC")
                    continue
                elif command == "curr?" or command == "curr:dc?" or command == "idc?":
                    self.sp.publish(reply_topic, self.current_as_string)
                    continue
                elif command == "curr_max?" or command == "curr:max?" or command == "imax?":
                    self.sp.publish(reply_topic, str(_NTP6531.NTP6531_CURRENT_HIGH_LIMIT) + " ADC")
                    continue
                elif command == "curr_min?" or command == "curr:min?" or command == "imin?":
                    self.sp.publish(reply_topic, str(_NTP6531.NTP6531_CURRENT_LOW_LIMIT) + " ADC")
                    continue
                elif command == "curr_limit_up?" or command == "curr:limit:up?" or command == "iup?":
                    self.sp.publish(reply_topic, str(self.current_limit_upper) + " ADC")
                    continue
                elif command == "curr_limit_up" or command == "curr:limit:up" or command == "iup":
                    # checking limits
                    if _NTP6531.NTP6531_CURRENT_HIGH_LIMIT >= value >= _NTP6531.NTP6531_CURRENT_LOW_LIMIT:
                        self.current_limit_upper = value
                        self.sp.publish(reply_topic, payload_accepted)
                        continue
                elif command == "curr_limit_low?" or command == "curr:limit:low?" or command == "ilow?":
                    self.sp.publish(reply_topic, str(self.current_limit_lower) + " ADC")
                    continue
                elif command == "curr_limit_low" or command == "curr:limit:low" or command == "ilow":
                    # checking limits
                    if _NTP6531.NTP6531_CURRENT_HIGH_LIMIT >= value >= _NTP6531.NTP6531_CURRENT_LOW_LIMIT:
                        self.current_limit_lower = value
                        self.sp.publish(reply_topic, str(payload_accepted))
                        continue
                # ------------------------------------------------------------------------------------------------
                # O T H E R commands - Handling
                # ------------------------------------------------------------------------------------------------
                elif command == "mode?":
                    self.sp.publish(topic=reply_topic, payload=self.source_mode)
                    continue
                elif command == "?":
                    self.sp.publish(reply_topic + "/manufactorer", self.manufactorer)
                    self.sp.publish(reply_topic + "/devicetype", self.devicetype)
                    self.sp.publish(reply_topic + "/model", self.model)
                    self.sp.publish(reply_topic + "/serialnumber", str(self.serialnumber))
                    self.sp.publish(reply_topic + "/commands", str(self.__commands))
                    continue
                elif command == "echo?" or command == "ping?":
                    self.sp.publish(reply_topic, str(datetime.datetime.utcnow()))
                    continue

                raise Exception("Command invalid")

            except Exception as e:
                self.sp.publish(reply_topic, str(p["payload_error"]) + ":" + str(e))
                continue
            finally:
                pass

