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
        self.commands = ["vdc?", "idc?", "vdc", "idc", "output"]

    def run(self) -> None:
        while True:
            time.sleep(0.025)
            # we exit this thread loop if the device have been unplugged
            if not self.connected():
                break
            try:
                match, data = self.mqtt.get(block=False)
                self.validate(match.string, data)
            except:
                continue

            try:
                if self.topic_cmd == "output":
                    if int(self.payload_float) == 0:
                        self.output_off()
                        self.sp.publish(self.topic_reply, self.payload_accepted)
                    else:
                        self.output_on()
                        self.sp.publish(self.topic_reply, self.payload_accepted)
                    continue
                # ------------------------------------------------------------------------------------------------
                # V O L T A G E self.topic_cmds - Handling
                # ------------------------------------------------------------------------------------------------
                elif self.topic_cmd == "volt?" or self.topic_cmd == "volt:dc?" or self.topic_cmd == "vdc?":
                    self.sp.publish(self.topic_reply, self.volt_as_string)
                    continue
                elif self.topic_cmd == "volt_applied?" or self.topic_cmd == "applied:volt:dc?" or self.topic_cmd == "applied_vdc?":
                    self.sp.publish(self.topic_reply, str(self.apply_volt) + " VDC")
                    continue
                elif self.topic_cmd == "volt" or self.topic_cmd == "volt:dc" or self.topic_cmd == "vdc":
                    # checking the self.payload_float limits
                    if _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT >= self.payload_float >= _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT:
                        self.apply_volt = self.payload_float
                        self.sp.publish(self.topic_reply, self.payload_accepted)
                        continue
                elif self.topic_cmd == "volt_max?" or self.topic_cmd == "volt:max?" or self.topic_cmd == "vmax?":
                    self.sp.publish(self.topic_reply, str(_NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT) + " VDC")
                    continue
                elif self.topic_cmd == "volt_min?" or self.topic_cmd == "volt:min?" or self.topic_cmd == "vmin?":
                    self.sp.publish(self.topic_reply, str(_NTP6531.NTP6531_VOLTAGE_LOW_LIMIT) + " VDC")
                    continue
                elif self.topic_cmd == "volt_limit_up?" or self.topic_cmd == "volt:limit:up?" or self.topic_cmd == "vup?":
                    self.sp.publish(self.topic_reply, str(self.volt_limit_upper) + " VDC")
                    continue
                elif self.topic_cmd == "volt_limit_up" or self.topic_cmd == "volt:limit:up" or self.topic_cmd == "vup":
                    # checking limits
                    if _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT >= self.payload_float >= _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT:
                        self.volt_limit_upper = self.payload_float
                        self.sp.publish(self.topic_reply, self.payload_accepted)
                        continue
                elif self.topic_cmd == "volt_limit_low?" or self.topic_cmd == "volt:limit:low?" or self.topic_cmd == "vlow?":
                    self.sp.publish(self.topic_reply, str(self.volt_limit_lower) + " VDC")
                    continue
                elif self.topic_cmd == "volt_limit_low" or self.topic_cmd == "volt:limit:low" or self.topic_cmd == "vlow":
                    # checking limits
                    if _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT >= self.payload_float >= _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT:
                        self.volt_limit_lower = self.payload_float
                        self.sp.publish(self.topic_reply, self.payload_accepted)
                        continue
                # ------------------------------------------------------------------------------------------------
                # C U R R E N T self.topic_cmds - Handling
                # ------------------------------------------------------------------------------------------------
                elif self.topic_cmd == "curr" or self.topic_cmd == "curr:dc" or self.topic_cmd == "idc":
                    # checking limits
                    if _NTP6531.NTP6531_CURRENT_HIGH_LIMIT >= self.payload_float >= _NTP6531.NTP6531_CURRENT_LOW_LIMIT:
                        self.apply_current = self.payload_float
                        self.sp.publish(self.topic_reply, self.payload_accepted)
                        continue
                elif self.topic_cmd == "curr_applied?" or self.topic_cmd == "applied:curr:dc?" or self.topic_cmd == "applied_idc?":
                    self.sp.publish(self.topic_reply, str(self.apply_current) + " ADC")
                    continue
                elif self.topic_cmd == "curr?" or self.topic_cmd == "curr:dc?" or self.topic_cmd == "idc?":
                    self.sp.publish(self.topic_reply, self.current_as_string)
                    continue
                elif self.topic_cmd == "curr_max?" or self.topic_cmd == "curr:max?" or self.topic_cmd == "imax?":
                    self.sp.publish(self.topic_reply, str(_NTP6531.NTP6531_CURRENT_HIGH_LIMIT) + " ADC")
                    continue
                elif self.topic_cmd == "curr_min?" or self.topic_cmd == "curr:min?" or self.topic_cmd == "imin?":
                    self.sp.publish(self.topic_reply, str(_NTP6531.NTP6531_CURRENT_LOW_LIMIT) + " ADC")
                    continue
                elif self.topic_cmd == "curr_limit_up?" or self.topic_cmd == "curr:limit:up?" or self.topic_cmd == "iup?":
                    self.sp.publish(self.topic_reply, str(self.current_limit_upper) + " ADC")
                    continue
                elif self.topic_cmd == "curr_limit_up" or self.topic_cmd == "curr:limit:up" or self.topic_cmd == "iup":
                    # checking limits
                    if _NTP6531.NTP6531_CURRENT_HIGH_LIMIT >= self.payload_float >= _NTP6531.NTP6531_CURRENT_LOW_LIMIT:
                        self.current_limit_upper = self.payload_float
                        self.sp.publish(self.topic_reply, self.payload_accepted)
                        continue
                elif self.topic_cmd == "curr_limit_low?" or self.topic_cmd == "curr:limit:low?" or self.topic_cmd == "ilow?":
                    self.sp.publish(self.topic_reply, str(self.current_limit_lower) + " ADC")
                    continue
                elif self.topic_cmd == "curr_limit_low" or self.topic_cmd == "curr:limit:low" or self.topic_cmd == "ilow":
                    # checking limits
                    if _NTP6531.NTP6531_CURRENT_HIGH_LIMIT >= self.payload_float >= _NTP6531.NTP6531_CURRENT_LOW_LIMIT:
                        self.current_limit_lower = self.payload_float
                        self.sp.publish(self.topic_reply, str(self.payload_accepted))
                        continue
                # ------------------------------------------------------------------------------------------------
                # O T H E R self.topic_cmds - Handling
                # ------------------------------------------------------------------------------------------------
                elif self.topic_cmd == "mode?":
                    self.sp.publish(topic=self.topic_reply, payload=self.source_mode)
                    continue
                raise Exception("Command invalid")

            except Exception as e:
                self.sp.publish(self.topic_reply, self.payload_error + ":" + str(e))
                continue
            finally:
                pass

