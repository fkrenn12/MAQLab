import datetime
import threading
import time
import Extensions
from external_modules.subpub import SubPub
from numpy import clip
import asyncio
# --------------------------------------------------------
from Devices.Manson import NTP6531 as _NTP6531


def anydef():
    print("ANYDEF")
    pass


class NTP6531(_NTP6531.NTP6531, Extensions.Device):

    def __init__(self, _port, _baudrate=9600):
        _NTP6531.NTP6531.__init__(self, _port, _baudrate)
        Extensions.Device.__init__(self)
        self.commands = ["vdc?", "idc?", "vdc", "idc", "output"]
        self.continous = False
        self.prev_continous = self.continous
        self.loop = asyncio.get_event_loop()
        self.__measure_task = None
        self.count = 0
        self.stop = False
        self.execute = Extensions.Execute_command()
        self.executions = list()

    def run(self) -> None:
        # mt = self.__loop.create_task(self.task_measure())

        # asyncio.run(self.task_measure())
        while True:
            time.sleep(0.01)
            # we exit this thread loop if the device have been unplugged
            if not self.connected():
                break
            try:
                topic, payload = self.read_from_mqtt()
                t = self.validate_topic(topic=topic)
                p = self.validate_payload(payload=payload)
                try:
                    self.execute_standard_commands(topic=topic, payload=payload, t=t, p=p)
                except:
                    # as standard command executed -> nothing more to do
                    raise Exception

                # ---------------------------
                # conditional creating thread
                # ---------------------------
                # check for available existing thread
                next_exe = None
                for exe in self.executions:
                    if not exe.executing:
                        next_exe = exe
                        break
                if next_exe is None:
                    # we need a new thread
                    next_exe = Extensions.Execute_command()
                    self.executions.append(next_exe)

                next_exe.data = self.command_data(t["command"], p)
                next_exe.executing = True
                try:
                    next_exe.start()
                except:
                    pass





                # topic, payload = self.handle_command(self.topic_cmd, self.payload_float)
                # self.sp.publish(topic, payload)
            except Exception:
                pass

            if self.continous != self.prev_continous:
                if self.continous:
                    try:
                        try:
                            self.execute.start()
                        except:
                            pass
                        self.execute.test = self.volt_as_string
                        self.execute.executing = True
                    except:
                        pass
                else:
                    # self.execute.kill()
                    self.execute.executing = False

            self.prev_continous = self.continous

            continue

    def command_data(self,command,p):
        repetitions = 1
        interval = 1

        return ({"handler": self.handle_command, "command": command, "repetitions": repetitions, "interval": interval, "payload" : p["float"]})

    # ------------------------------------------------------------------------------------------------
    # COMMAND - Handler
    # ------------------------------------------------------------------------------------------------
    def handle_command(self, topic, payload_float):
        try:
            if topic == "output":
                if int(payload_float) == 0 or int(payload_float) == 1:
                    if int(payload_float) == 0:
                        self.output_off()
                    elif int(payload_float) == 1:
                        self.output_on()
                    return self.topic_reply, self.payload_accepted
                return self.topic_reply, self.payload_error
            # ------------------------------------------------------------------------------------------------
            # V O L T A G E - Handling
            # ------------------------------------------------------------------------------------------------
            elif topic == "vdc?":
                x = eval("self.volt_as_string")
                # return self.topic_reply, self.volt_as_string
                return self.topic_reply, x
            elif topic == "applied_vdc?":
                return self.topic_reply, str(self.apply_volt) + " VDC"

            elif topic == "vdc":
                # checking the self.payload_float limits
                val = clip(self.payload_float, _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT, _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT)
                val = clip(val, self.volt_limit_lower, self.volt_limit_upper)
                self.apply_volt = val
                if val == self.payload_float:
                    return self.topic_reply, self.payload_accepted
                return self.topic_reply, self.payload_limited

            elif topic == "vmax?":
                return self.topic_reply, str(_NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT) + " VDC"

            elif topic == "vmin?":
                return self.topic_reply, str(_NTP6531.NTP6531_VOLTAGE_LOW_LIMIT) + " VDC"

            elif topic == "vlimit_up?":
                return self.topic_reply, str(self.volt_limit_upper) + " VDC"

            elif topic == "vlimit_up":
                # checking limits
                val = clip(self.payload_float, _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT, _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT)
                self.volt_limit_upper = val
                if self.payload_float == val:
                    return self.topic_reply, self.payload_accepted
                return self.topic_reply, self.payload_limited

            elif topic == "vlimit_low?":
                return self.topic_reply, str(self.volt_limit_lower) + " VDC"

            elif topic == "vlimit_low":
                # checking limits
                val = clip(self.payload_float, _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT, _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT)
                self.volt_limit_lower = val
                if self.payload_float == val:
                    return self.topic_reply, self.payload_accepted
                return self.topic_reply, self.payload_limited

            # ------------------------------------------------------------------------------------------------
            # C U R R E N T - Handling
            # ------------------------------------------------------------------------------------------------
            elif topic == "idc":
                # checking limits
                val = clip(self.payload_float, _NTP6531.NTP6531_CURRENT_LOW_LIMIT, _NTP6531.NTP6531_CURRENT_HIGH_LIMIT)
                val = clip(val, self.current_limit_lower, self.current_limit_upper)
                self.apply_current = val
                if self.payload_float == val:
                    return self.topic_reply, self.payload_accepted
                return self.topic_reply, self.payload_limited

            elif topic == "applied_idc?":
                return self.topic_reply, str(self.apply_current) + " ADC"

            elif topic == "idc?":
                return self.topic_reply, self.current_as_string

            elif topic == "imax?":
                return self.topic_reply, str(_NTP6531.NTP6531_CURRENT_HIGH_LIMIT) + " ADC"

            elif topic == "imin?":
                return self.topic_reply, str(_NTP6531.NTP6531_CURRENT_LOW_LIMIT) + " ADC"

            elif topic == "ilimit_up?":
                return self.topic_reply, str(self.current_limit_upper) + " ADC"

            elif topic == "ilimit_up":
                # checking limits
                val = clip(self.payload_float, _NTP6531.NTP6531_CURRENT_LOW_LIMIT, _NTP6531.NTP6531_CURRENT_HIGH_LIMIT)
                self.current_limit_upper = val
                if self.payload_float == val:
                    return self.topic_reply, self.payload_accepted
                return self.topic_reply, self.payload_limited

            elif topic == "ilimit_low?":
                return self.topic_reply, str(self.current_limit_lower) + " ADC"

            elif topic == "ilimit_low":
                # checking limits
                val = clip(self.payload_float, _NTP6531.NTP6531_CURRENT_LOW_LIMIT, _NTP6531.NTP6531_CURRENT_HIGH_LIMIT)
                self.current_limit_lower = val
                if self.payload_float == val:
                    return self.topic_reply, self.payload_accepted
                return self.topic_reply, self.payload_limited

            # ------------------------------------------------------------------------------------------------
            # O T H E R - Handling
            # ------------------------------------------------------------------------------------------------
            elif topic == "cmode?":
                return self.topic_reply, self.source_mode

            elif topic == "disable_hsm":
                self.disable_human_safety_mode()
                return self.topic_reply, self.payload_accepted

            elif topic == "@vdc?":
                self.continous = True
                return self.topic_reply, self.payload_accepted

            elif topic == "!@vdc?":
                self.continous = False
                return self.topic_reply, self.payload_accepted

        except Exception as e:
            return self.topic_reply, self.payload_error + ":" + str(e)

        # here we if no valid command was detected
        return self.topic_reply, self.payload_command_error
