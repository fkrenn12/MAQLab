import threading
import datetime

import numpy
import time
import shared as s
import Extensions
import copy
import json
from numpy import clip

HANDLER_STATUS_VALUE = "val"
HANDLER_STATUS_ACCEPTED = "accept"
HANDLER_STATUS_LIMITED = "limited"
HANDLER_STATUS_COMMAND_ERROR = "command_error"
HANDLER_STATUS_PAYLOAD_ERROR = "payload_error"


class Data:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def add(self, **kwargs):
        self.__dict__.update(kwargs)


class ExecuterConfiguration:
    def __init__(self):
        self.data = None


class ExecuterClient:
    def __init__(self):
        self.x = 0


class ExecuterState:
    def __init__(self):
        self.x = 0


# --------------------------------------------------------------------------
# Measure Executer Thread
# --------------------------------------------------------------------------
class Executer(threading.Thread):
    def __init__(self, subpub, master_lock):
        super().__init__()
        self.__lock = threading.Lock()
        self.__master_lock = master_lock
        self.__sp = subpub
        self.config = ExecuterConfiguration()
        self.__clients = list()
        self.__running = False
        self.__exe_counter = 0
        self.to_run = None
        self.prepared = None
        self.handler = None
        self.__time_of_start = 0

    def run(self):

        while True:
            time.sleep(0.01)
            with self.__lock:
                running = self.__running
            if running:
                # timestamp = str(datetime.datetime.utcnow())
                try:
                    if hasattr(self.handler, '__call__'):
                        print("Executing:" + self.to_run.command + " " + str(self.__exe_counter))
                        with self.__master_lock:
                            status, value = self.handler(self.to_run.command, self.to_run.payload)
                            if status == HANDLER_STATUS_VALUE:
                                self.__sp.publish(self.prepared.reply, str(value))
                            elif status == HANDLER_STATUS_ACCEPTED:
                                self.__sp.publish(self.prepared.reply, self.prepared.accepted + "," + str(value))
                            elif status == HANDLER_STATUS_LIMITED:
                                self.__sp.publish(self.prepared.reply, self.prepared.limited + "," + str(value))
                            elif status == HANDLER_STATUS_COMMAND_ERROR:
                                self.__sp.publish(self.prepared.reply,
                                                  self.prepared.command_error + "," + str(time.time()))
                                raise Exception
                            elif status == HANDLER_STATUS_PAYLOAD_ERROR:
                                self.__sp.publish(self.prepared.reply,
                                                  self.prepared.error + " " + value + "," + str(time.time()))
                                raise Exception
                            else:
                                self.__sp.publish(self.prepared.reply, "Internal Error - stopped " + str(time.time()))
                                raise Exception
                except:
                    with self.__lock:
                        self.__running = False

                self.__exe_counter += 1

                print((time.time() - self.__time_of_start) / 60)

                if 0 < self.to_run.repetitions <= self.__exe_counter or (time.time() - self.__time_of_start) / 60 > 1:
                    with self.__lock:
                        self.__running = False
                else:
                    time.sleep(self.to_run.interval)

            else:
                pass

    def __get_running(self):
        with self.__lock:
            value = self.__running
        return value

    def __set_running(self, value):
        with self.__lock:
            self.__running = value
            self.__exe_counter = 0
            if value:
                self.__time_of_start = time.time()

    def __get_sol(self):
        return False

    def __set_sol(self, value):
        with self.__lock:
            self.__time_of_start = time.time()

    running = property(__get_running, __set_running)
    sign_of_life = property(__get_sol, __set_sol)


# --------------------------------------------------------------------------
# Connected Device Thread
# --------------------------------------------------------------------------
class Device(threading.Thread):
    def __init__(self):
        super().__init__()
        self.__comport = ""
        self.__invent_number = "0"
        self.commands = []
        self.sp = None
        self.mqtt = None

        self.__master_lock = threading.Lock()
        self.__measure_lock = threading.Lock()
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
                prepared = self.validate_topic(topic=topic)
                prepared.__dict__.update(self.validate_payload(payload=payload).__dict__)
                try:
                    self.execute_standard_commands(data=prepared)
                except:
                    # as standard command executed -> nothing more to do
                    raise Exception

                # ---------------------------
                # conditioned creating thread
                # ---------------------------
                # check for available existing executor thread
                executor = None
                for a_executor in self.executions:
                    if not a_executor.running:
                        executor = a_executor
                        break

                if executor is None:
                    # nothing found so we need a new thread
                    executor = Extensions.Executer(subpub=self.sp, master_lock=self.__master_lock)
                    # adding to the list
                    with self.__measure_lock:
                        self.executions.append(executor)

                # generate running conditions fpr the measure executer
                # and copy it to thread
                executor.prepared = copy.deepcopy(prepared)
                executor.to_run = copy.deepcopy(self.to_run(data=prepared))
                executor.handler = self.handler
                executor.running = True
                try:
                    executor.start()
                except:
                    pass
                del prepared

                print("#Threads:" + str(len(self.executions)))
            except Exception:
                pass

            continue

    # --------------------------------------------------------
    #  CREATED
    # --------------------------------------------------------
    def on_created(self, port, invent_number, sp):
        self.__comport = str(port)
        self.__invent_number = invent_number
        self.sp = sp  # subpub object
        print(str(datetime.datetime.now()) + "  :" + self.devicetype + " " + self.model + " plugged into "
              + self.__comport + ", Accessnumber is: " + str(invent_number))
        # subscribe to the internal subpub mqtt-broker
        # we use regular expressions
        # \A start (.+) beliebig und mindestens ein Zeichen (.+)$ beliebig und mindestens ein Zeichen und ein Ende
        # | bedeutet "oder" \? ist das Zeichen "?" weil ? in regex eine Bedeutung hat
        self.mqtt = sp.subscribe("(\A(.+)/cmd/" + self.__invent_number + "/(.+)$)|(\A(.+)cmd/\?$)")

    # --------------------------------------------------------
    #  READ FROM MQTT queue
    # --------------------------------------------------------
    def read_from_mqtt(self):
        try:
            match, data = self.mqtt.get(block=False)
            return match.string, data
            # self.validate(match.string, data)
        except:
            raise Exception

    # --------------------------------------------------------
    #  V A L I D A T E
    # --------------------------------------------------------
    def execute_standard_commands(self, data):
        try:
            if data.command == s.topic_access_number:
                self.sp.publish(data.reply, str(self.__invent_number))
                raise Exception

            # if data.matching:
            # matching the accessnumber, we handle the standard commands
            # we check the running measurement threads for a sign of life
            with self.__measure_lock:
                for executor in self.executions:
                    if executor.running:
                        print("session-id: " + executor.to_run.session_id)
                        if executor.to_run.session_id == data.session_id:
                            executor.sign_of_life = True

            if data.command == "?":
                self.sp.publish(data.reply + "/manufactorer", self.manufactorer)
                self.sp.publish(data.reply + "/devicetype", self.devicetype)
                self.sp.publish(data.reply + "/model", self.model)
                self.sp.publish(data.reply + "/serialnumber", str(self.serialnumber))
                self.sp.publish(data.reply + "/commands", str(self.commands))
                raise Exception

            elif data.command == "echo?" or data.command == "ping?":
                self.sp.publish(data.reply, str(datetime.datetime.utcnow()))
                raise Exception

            elif data.command == "hsm_off":
                try:
                    self.disable_human_safety_mode()
                except:
                    pass
                self.sp.publish(data.reply, "0")
                raise Exception
            return
            # else:
            # accessnumber is not matching
            # this case is not possible in fact, so we must
            #    return
        except:
            raise Exception

    # --------------------------------------------------------
    #  V A L I D A T E  incoming  T O P I C
    # --------------------------------------------------------
    def validate_topic(self, topic):
        matching = False
        try:
            topic = topic.decode("utf-8")
        except:
            pass

        try:
            topic = topic.lower()
            topic_splitted = topic.split("/")
        except:
            raise Exception

        split_count = len(topic_splitted)
        if 3 <= split_count < 7 and topic_splitted[0] == s.topic_root:
            try:
                # the section after the root contains the session_id
                session_id = topic_splitted[1]
                index_of_cmd = topic_splitted.index(s.topic_cmd)
                reply_topic = topic.replace(s.topic_cmd, s.topic_reply)
                if topic_splitted[index_of_cmd + 1] == s.topic_request:
                    command = s.topic_access_number
                    reply_topic = reply_topic.replace(s.topic_request, "")
                    reply_topic = reply_topic + self.model + "/" + s.topic_access_number
                else:
                    command = topic_splitted[index_of_cmd + 2]
                    command = command.replace("1", "")
                    command = command.replace(" ", "")
                    if topic_splitted[index_of_cmd + 1] == str(self.__invent_number):
                        matching = True
                # return {"topic": topic, "command": command, "reply": reply_topic, "matching": matching}
                return Data(topic=topic,
                            command=command,
                            session_id=session_id,
                            reply=reply_topic,
                            matching=matching)
            except:
                raise Exception
        else:
            raise Exception

    # --------------------------------------------------------
    #  V A L I D A T E  incoming  P A Y L O A D
    # --------------------------------------------------------
    def validate_payload(self, payload):
        payload_error = s.payload_error
        payload_accepted = s.payload_accepted
        payload_limited = s.payload_limited
        payload_command_error = s.payload_command_error
        payload_float = 0
        payload_dict = dict()
        try:
            try:
                payload = payload.decode("utf-8")
            except:
                pass
            try:
                payload = payload.strip(" ")
                payload.replace("'", "\"")
                if not (str(payload).startswith("{") and str(payload).endswith("}")):
                    raise
                payload_dict = json.loads(payload)

                # payload_json = obj
            except:
                # it is not json
                # print("NO JSON")
                if payload == "":
                    payload = "0"
                try:
                    payload_float = float(payload)
                except:
                    payload_float = 0.0

            return Data(error=payload_error,
                        accepted=payload_accepted,
                        limited=payload_limited,
                        command_error=payload_command_error,
                        float=payload_float,
                        dict=payload_dict)
        except:
            raise

    # ------------------------------------------------------------------------------------------------
    # RUNNING configuration
    # ------------------------------------------------------------------------------------------------
    def to_run(self, data):
        repetitions = 1
        interval = 1

        try:
            repetitions = data.dict['reps']
        except:
            pass
        try:
            interval = data.dict['interval']
        except:
            pass

        return Extensions.Data(
            session_id=data.session_id,
            command=data.command,
            repetitions=repetitions,
            interval=interval,
            payload=data.float)

    # --------------------------------------------------------
    #  DESTROYED
    # --------------------------------------------------------
    def on_destroyed(self):
        print(str(datetime.datetime.now()) + "  :" + self.model + " removed from " + self.__comport)
        self.__comport = ""

    def __get_accessnumber(self):
        return self.__invent_number

    accessnumber = property(__get_accessnumber)


def limiter(value, limits_low, limits_high):
    value_orig = value
    try:
        if type(limits_low) is not list:
            limits_low = list(limits_low)
        if type(limits_high) is not list:
            limits_high = list(limits_high)
        try:
            for ll in limits_low:
                value = numpy.clip(value, ll, float('inf'))
        except:
            pass
        try:
            for hl in limits_high:
                value = numpy.clip(value, float('-inf'), hl)
        except:
            pass

        return bool(value != value_orig), value
    except:
        return False, value_orig
