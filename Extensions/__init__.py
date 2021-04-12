import threading
import datetime


class Device(threading.Thread):
    def __init__(self):
        super().__init__()

    def on_created(self, comport, invent_number):
        self.__comport = str(comport)
        self.__invent_number = invent_number
        print(str(datetime.datetime.now()) + "  :" + self.devicetype + " " + self.model + " HOHO plugged into " + self.__comport + ", Accessnumber is: "
              + str(invent_number))

    def on_destroyed(self):
        print(str(datetime.datetime.now()) + "  :" + self.model + " removed from " + self.__comport)
        self.__comport = ""


