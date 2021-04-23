# --------------------------------------------------------
from Devices.BKPrecision import E2831 as _E2831
import Extensions
import math
import threading


class BK2831E(_E2831.BK2831E, Extensions.Device):

    def __init__(self, _port, _baudrate=9600):
        _E2831.BK2831E.__init__(self, _port, _baudrate)
        Extensions.Device.__init__(self)
        self.__commands = ["vdc?", "idc?", "vac?", "iac?", "res?", "f?", "pdc?"]  # TODO: noch nicht komplett
        # self.__lllock = threading.Lock()

    # ------------------------------------------------------------------------------------------------
    # COMMAND - Handler
    # ------------------------------------------------------------------------------------------------
    def handler(self, command, value):
        # with self.__lllock:
        try:
            # ------------------------------------------------------------------------------------------------
            # V O L T A G E - Handling
            # ------------------------------------------------------------------------------------------------
            if command == "vdc?":
                # return self.command_reply, self.volt_as_string
                self.set_mode_vdc_auto_range()
                self.measure()
                return Extensions.HANDLER_STATUS_VALUE, self.volt_as_string

            elif command == "vac?":
                self.set_mode_vac_auto_range()
                self.measure()
                return Extensions.HANDLER_STATUS_VALUE, self.volt_as_string

            elif command == "vrms?":
                self.set_mode_vdc_auto_range()
                self.measure()
                vdc = self.volt
                self.set_mode_vac_auto_range()
                self.measure()
                vac = self.volt
                vrms = math.sqrt(math.pow(vac, 2) + math.pow(vdc, 2))
                return Extensions.HANDLER_STATUS_VALUE, "{:.6f}".format(vrms) + " VRMS"

            elif command == "idc?":
                self.set_mode_idc_range_20A()
                self.measure()
                return Extensions.HANDLER_STATUS_VALUE, self.current_as_string

            elif command == "iac?":
                self.set_mode_iac_range_20A()
                self.measure()
                return Extensions.HANDLER_STATUS_VALUE, self.current_as_string

            elif command == "irms?":
                self.set_mode_idc_range_20A()
                self.measure()
                idc = self.current
                self.set_mode_iac_range_20A()
                self.measure()
                iac = self.current
                irms = math.sqrt(math.pow(iac, 2) + math.pow(idc, 2))
                return Extensions.HANDLER_STATUS_VALUE, "{:.6f}".format(irms) + " ARMS"

            elif command == "idc_200m?":
                self.set_mode_idc_range_200mA()
                self.measure()
                return Extensions.HANDLER_STATUS_VALUE, self.current_as_string

            elif command == "iac_200m?":
                self.set_mode_iac_range_200mA()
                self.measure()
                return Extensions.HANDLER_STATUS_VALUE, self.current_as_string

            elif command == "f?":
                self.set_mode_frequency_auto_range()
                self.measure()
                return Extensions.HANDLER_STATUS_VALUE, self.frequence_as_string

            elif command == "periode?":
                self.set_mode_periode_auto_range()
                self.measure()
                return Extensions.HANDLER_STATUS_VALUE, self.periode_as_string

            elif command == "res?" or command == "r?":
                self.set_mode_resistance_auto_range()
                self.measure()
                return Extensions.HANDLER_STATUS_VALUE, self.resistance_as_string

            elif command == "pdc?":
                self.set_mode_vdc_auto_range()
                self.measure()
                vdc = self.volt
                self.set_mode_idc_range_20A()
                self.measure()
                idc = self.current
                power = vdc * idc
                return Extensions.HANDLER_STATUS_VALUE, "{:.6f}".format(power) + " WDC"

            elif command == "pac?":
                self.set_mode_vac_auto_range()
                self.measure()
                vac = self.volt
                self.set_mode_iac_range_20A()
                self.measure()
                iac = self.current
                power = vac * iac
                return Extensions.HANDLER_STATUS_VALUE, "{:.6f}".format(power) + " WAC"

        except Exception as e:
            return Extensions.HANDLER_STATUS_PAYLOAD_ERROR, str(e)
