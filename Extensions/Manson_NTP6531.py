from Devices.Manson import NTP6531 as _NTP6531
import datetime
import threading
import time
import Extensions
from numpy import clip
import copy


class NTP6531(_NTP6531.NTP6531, Extensions.Device):

    def __init__(self, _port, _baudrate=9600):
        _NTP6531.NTP6531.__init__(self, _port, _baudrate)
        Extensions.Device.__init__(self)
        self.__main_lock = threading.Lock()
        self.commands = ["vdc?", "idc?", "vdc", "idc", "output"]
        self.__measure_task = None
        self.count = 0
        self.stop = False
        self.executions = list()

    def run(self) -> None:
        while True:
            time.sleep(0.01)
            # we exit this thread loop if the device has been unplugged
            if not self.connected():
                break
            try:
                topic, payload = self.read_from_mqtt()
                data_reply = self.validate_topic(topic=topic)
                data_reply.__dict__.update(self.validate_payload(payload=payload).__dict__)
                try:
                    self.execute_standard_commands(data=data_reply)
                except:
                    # as standard command executed -> nothing more to do
                    raise Exception

                # ---------------------------
                # conditioned creating thread
                # ---------------------------
                # check for available existing thread
                next_exe = None
                for exe in self.executions:
                    if not exe.executing:
                        next_exe = exe
                        break
                if next_exe is None:
                    # we need a new thread
                    next_exe = Extensions.Execute_command(self.__main_lock)
                    self.executions.append(next_exe)
                    next_exe.sp = self.sp

                next_exe.data_reply = copy.deepcopy(data_reply)
                next_exe.data_measure = copy.deepcopy(self.command_data(data=data_reply))
                next_exe.handler = self.handle_command
                next_exe.executing = True
                try:
                    next_exe.start()
                except:
                    pass
                del data_reply

                print("#Threads:" + str(len(self.executions)))
            except Exception:
                pass

            continue

    # ------------------------------------------------------------------------------------------------
    # COMMAND DATA
    # ------------------------------------------------------------------------------------------------
    def command_data(self, data):
        repetitions = 1
        interval = 2
        return Extensions.Data(
            command=data.command,
            repetitions=repetitions,
            interval=interval,
            payload=data.float)

    # ------------------------------------------------------------------------------------------------
    # COMMAND - Handler
    # ------------------------------------------------------------------------------------------------
    def handle_command(self, topic, value):
        try:
            if topic == "output":
                if int(value) == 0 or int(value) == 1:
                    if int(value) == 0:
                        self.output_off()
                    elif int(value) == 1:
                        self.output_on()
                    return Extensions.HANDLER_STATUS_ACCEPTED, 0
                return Extensions.HANDLER_STATUS_PAYLOAD_ERROR, 0
            # ------------------------------------------------------------------------------------------------
            # V O L T A G E - Handling
            # ------------------------------------------------------------------------------------------------
            elif topic == "vdc?":
                # return self.topic_reply, self.volt_as_string
                return Extensions.HANDLER_STATUS_VALUE, self.volt_as_string

            elif topic == "applied_vdc?":
                return Extensions.HANDLER_STATUS_VALUE, str(self.apply_volt) + " VDC"

            elif topic == "vdc":
                # checking the value limits
                clipped = clip(value, _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT, _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT)
                clipped = clip(clipped, self.volt_limit_lower, self.volt_limit_upper)
                self.apply_volt = clipped
                if clipped == value:
                    return Extensions.HANDLER_STATUS_ACCEPTED, 0
                return Extensions.HANDLER_STATUS_LIMITED, 0

            elif topic == "vmax?":
                return Extensions.HANDLER_STATUS_VALUE, str(_NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT) + " VDC"

            elif topic == "vmin?":
                return Extensions.HANDLER_STATUS_VALUE, str(_NTP6531.NTP6531_VOLTAGE_LOW_LIMIT) + " VDC"

            elif topic == "vlimit_up?":
                return Extensions.HANDLER_STATUS_VALUE, str(self.volt_limit_upper) + " VDC"

            elif topic == "vlimit_up":
                # checking limits
                clipped = clip(value, _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT, _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT)
                self.volt_limit_upper = clipped
                if value == clipped:
                    return Extensions.HANDLER_STATUS_ACCEPTED, 0
                return Extensions.HANDLER_STATUS_LIMITED, 0

            elif topic == "vlimit_low?":
                return Extensions.HANDLER_STATUS_VALUE, str(self.volt_limit_lower) + " VDC"

            elif topic == "vlimit_low":
                # checking limits
                clipped = clip(value, _NTP6531.NTP6531_VOLTAGE_LOW_LIMIT, _NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT)
                self.volt_limit_lower = clipped
                if value == clipped:
                    return Extensions.HANDLER_STATUS_ACCEPTED, 0
                return Extensions.HANDLER_STATUS_LIMITED, 0

            # ------------------------------------------------------------------------------------------------
            # C U R R E N T - Handling
            # ------------------------------------------------------------------------------------------------
            elif topic == "idc":
                # checking limits
                clipped = clip(value, _NTP6531.NTP6531_CURRENT_LOW_LIMIT, _NTP6531.NTP6531_CURRENT_HIGH_LIMIT)
                clipped = clip(clipped, self.current_limit_lower, self.current_limit_upper)
                self.apply_current = clipped
                if value == clipped:
                    return Extensions.HANDLER_STATUS_ACCEPTED, 0
                return Extensions.HANDLER_STATUS_LIMITED, 0

            elif topic == "applied_idc?":
                return Extensions.HANDLER_STATUS_VALUE, str(self.apply_current) + " ADC"

            elif topic == "idc?":
                return Extensions.HANDLER_STATUS_VALUE, self.current_as_string

            elif topic == "imax?":
                return Extensions.HANDLER_STATUS_VALUE, str(_NTP6531.NTP6531_CURRENT_HIGH_LIMIT) + " ADC"

            elif topic == "imin?":
                return Extensions.HANDLER_STATUS_VALUE, str(_NTP6531.NTP6531_CURRENT_LOW_LIMIT) + " ADC"

            elif topic == "ilimit_up?":
                return Extensions.HANDLER_STATUS_VALUE, str(self.current_limit_upper) + " ADC"

            elif topic == "ilimit_up":
                # checking limits
                clipped = clip(value, _NTP6531.NTP6531_CURRENT_LOW_LIMIT, _NTP6531.NTP6531_CURRENT_HIGH_LIMIT)
                self.current_limit_upper = clipped
                if value == clipped:
                    return Extensions.HANDLER_STATUS_ACCEPTED, 0
                return Extensions.HANDLER_STATUS_LIMITED, 0

            elif topic == "ilimit_low?":
                return Extensions.HANDLER_STATUS_VALUE, str(self.current_limit_lower) + " ADC"

            elif topic == "ilimit_low":
                # checking limits
                clipped = clip(value, _NTP6531.NTP6531_CURRENT_LOW_LIMIT, _NTP6531.NTP6531_CURRENT_HIGH_LIMIT)
                self.current_limit_lower = clipped
                if value == clipped:
                    return Extensions.HANDLER_STATUS_ACCEPTED, 0
                return Extensions.HANDLER_STATUS_LIMITED, 0

            # ------------------------------------------------------------------------------------------------
            # O T H E R - Handling
            # ------------------------------------------------------------------------------------------------
            elif topic == "cmode?":
                return Extensions.HANDLER_STATUS_VALUE, self.source_mode

            elif topic == "disable_hsm":
                self.disable_human_safety_mode()
                return Extensions.HANDLER_STATUS_ACCEPTED, 0

        except Exception as e:
            return Extensions.HANDLER_STATUS_PAYLOAD_ERROR, str(e)

        # here we if no valid command was detected
        return Extensions.HANDLER_STATUS_COMMAND_ERROR, 0
