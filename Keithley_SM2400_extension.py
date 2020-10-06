# --------------------------------------------------------
from Devices.Keithley import SM2400


# --------------------------------------------------------
class SM2400(SM2400.SM2400):

    def __init__(self, _port, _baudrate=9600):
        super().__init__(_port, _baudrate)

    @staticmethod
    def mqttmessage(_msg):
        pass

    def on_created(self):
        print("SM2400 Ser:" + str(self.serialnumber) + "plugged in")

    def on_destroyed(self):
        print("SM2400 removed")

    def execute(self):
        pass
