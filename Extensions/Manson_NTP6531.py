from Devices.Manson import NTP6531 as _NTP6531
import Extensions
from Extensions import limiter


class NTP6531(_NTP6531.NTP6531, Extensions.Device):
    def __init__(self, _port, _baudrate=9600):
        eval("_NTP6531.NTP6531.__init__(self, _port, _baudrate)")
        eval("Extensions.Device.__init__(self)")
        self.commands = ["output_on", "output_off",
                         "vdc?", "vdc", "vdc_applied?", "vdc_max?", "vdc_min?", "vdc_low?",
                         "vdc_low", "vdc_high?", "vdc_high",
                         "idc?", "idc", "idc_applied?", "idc_max?", "idc_min?", "idc_low?",
                         "idc_low", "idc_high?", "idc_high",
                         "pdc?", "cmode?", "disable_hsm"]

        # prepared for future use, first solutions for dynamically importable devices
        self.commands_dict = {"output_on": {"set_func": "output_on()", "return": 1},
                              "output_off": {"set_func": "output_off()", "return": 0}}  # ,
        # "vdc?": {"get_property": "volt_as_string", "return": "result"},
        # "vdc": {"set_property": "apply_volt = %value%", "return": "result"}}

        '''
         ,
                         "vdc?", "vdc", "vdc_applied?", "vdc_max?", "vdc_min?", "vdc_low?",
                         "vdc_low", "vdc_high?", "vdc_high",
                         "idc?", "idc", "idc_applied?", "idc_max?", "idc_min?", "idc_low?",
                         "idc_low", "idc_high?", "idc_high",
                         "pdc?", "cmode?", "disable_hsm"
        '''

    # ------------------------------------------------------------------------------------------------
    # COMMAND - Handler
    # ------------------------------------------------------------------------------------------------
    def handler(self, command, value):
        try:
            if command not in self.commands:
                return Extensions.HANDLER_STATUS_COMMAND_ERROR, 0

            commands = self.commands_dict.keys()
            if command in commands:
                t = self.commands_dict[command]
                try:
                    x = "self." + t["set_func"]
                    eval(x)
                    return Extensions.HANDLER_STATUS_ACCEPTED, str(t["return"])
                except:
                    pass

                try:
                    x = "self." + t["get_property"]
                    return Extensions.HANDLER_STATUS_VALUE, eval(x)
                except:
                    pass

                try:
                    x = "self." + t["set_property"].replace("%value%", str(value))
                    eval(x)
                    return Extensions.HANDLER_STATUS_VALUE,
                except:
                    pass

            '''    
            print(commands)
            if command == "output_on":
                self.output_on()
                return Extensions.HANDLER_STATUS_ACCEPTED, 1

            if command == "output_off":
                self.output_on()
                return Extensions.HANDLER_STATUS_ACCEPTED, 0
            '''

            # ------------------------------------------------------------------------------------------------
            # V O L T A G E - Handling
            # ------------------------------------------------------------------------------------------------
            if command == "vdc?":
                # return self.command_reply, self.volt_as_string
                return eval("Extensions.HANDLER_STATUS_VALUE"), eval("self.volt_as_string")

            elif command == "vdc_applied?":
                return Extensions.HANDLER_STATUS_VALUE, str(eval("self.apply_volt")) + " VDC"

            elif command == "vdc":
                self.apply_volt = value
                if value != self.apply_volt:
                    return Extensions.HANDLER_STATUS_LIMITED, self.apply_volt
                return Extensions.HANDLER_STATUS_ACCEPTED, value

            elif command == "vdc_max?":
                return Extensions.HANDLER_STATUS_VALUE, str(_NTP6531.NTP6531_VOLTAGE_HIGH_LIMIT) + " VDC"

            elif command == "vdc_min?":
                return Extensions.HANDLER_STATUS_VALUE, str(_NTP6531.NTP6531_VOLTAGE_LOW_LIMIT) + " VDC"

            elif command == "vdc_high?":
                return Extensions.HANDLER_STATUS_VALUE, str(self.volt_limit_high) + " VDC"

            elif command == "vdc_high":
                # checking limits
                self.volt_limit_high = value
                if value != self.volt_limit_high:
                    return Extensions.HANDLER_STATUS_LIMITED, self.volt_limit_high
                return Extensions.HANDLER_STATUS_ACCEPTED, value

            elif command == "vdc_low?":
                return Extensions.HANDLER_STATUS_VALUE, str(self.volt_limit_low) + " VDC"

            elif command == "vdc_low":
                # checking limits
                self.volt_limit_low = value
                if value != self.volt_limit_low:
                    return Extensions.HANDLER_STATUS_LIMITED, self.volt_limit_low
                return Extensions.HANDLER_STATUS_ACCEPTED, value

            # ------------------------------------------------------------------------------------------------
            # C U R R E N T - Handling
            # ------------------------------------------------------------------------------------------------
            elif command == "idc":
                # checking the value limits
                self.apply_current = value
                if value != self.apply_current:
                    return Extensions.HANDLER_STATUS_LIMITED, self.apply_current
                return Extensions.HANDLER_STATUS_ACCEPTED, value

            elif command == "idc_applied?":
                return Extensions.HANDLER_STATUS_VALUE, str(self.apply_current) + " ADC"

            elif command == "idc?":
                return Extensions.HANDLER_STATUS_VALUE, self.current_as_string

            elif command == "idc_max?":
                return Extensions.HANDLER_STATUS_VALUE, str(_NTP6531.NTP6531_CURRENT_HIGH_LIMIT) + " ADC"

            elif command == "idc_min?":
                return Extensions.HANDLER_STATUS_VALUE, str(_NTP6531.NTP6531_CURRENT_LOW_LIMIT) + " ADC"

            elif command == "idc_high?":
                return Extensions.HANDLER_STATUS_VALUE, str(self.current_limit_high) + " ADC"

            elif command == "idc_high":
                self.current_limit_high = value
                if value != self.current_limit_high:
                    return Extensions.HANDLER_STATUS_LIMITED, self.current_limit_high
                return Extensions.HANDLER_STATUS_ACCEPTED, value

            elif command == "idc_low?":
                return Extensions.HANDLER_STATUS_VALUE, str(self.current_limit_low) + " ADC"

            elif command == "idc_low":
                self.current_limit_low = value
                if value != self.current_limit_low:
                    return Extensions.HANDLER_STATUS_LIMITED, self.current_limit_low
                return Extensions.HANDLER_STATUS_ACCEPTED, value

            # ------------------------------------------------------------------------------------------------
            # POWER - Handling
            # ------------------------------------------------------------------------------------------------
            elif command == "pdc?":
                return Extensions.HANDLER_STATUS_VALUE, self.power_as_string
            # ------------------------------------------------------------------------------------------------
            # O T H E R - Handling
            # ------------------------------------------------------------------------------------------------
            elif command == "cmode?":
                return Extensions.HANDLER_STATUS_VALUE, self.source_mode

        except Exception as e:
            return Extensions.HANDLER_STATUS_PAYLOAD_ERROR, str(e)
