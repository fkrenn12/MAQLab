import threading
import datetime
import time
import shared as s
import Extensions
import copy

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


class Executer(threading.Thread):
    def __init__(self, subpub, main_lock):
        super().__init__()
        self.__lock = threading.Lock()
        self.__main_lock = main_lock
        self.__sp = subpub
        self.__running = False
        self.__exe_counter = 0
        self.to_run = None
        self.prepared = None

        self.handler = None

    def run(self):

        while True:
            time.sleep(0.01)
            with self.__lock:
                running = self.__running
            if running:
                timestamp = str(datetime.datetime.utcnow())
                try:
                    if hasattr(self.handler, '__call__'):
                        print("Executing:" + self.to_run.command + " " + str(self.__exe_counter))
                        with self.__main_lock:
                            status, value = self.handler(self.to_run.command, self.to_run.payload)
                            if status == HANDLER_STATUS_VALUE:
                                self.__sp.publish(self.prepared.reply, str(value))
                            elif status == HANDLER_STATUS_ACCEPTED:
                                self.__sp.publish(self.prepared.reply, self.prepared.accepted + " " + timestamp)
                            elif status == HANDLER_STATUS_LIMITED:
                                self.__sp.publish(self.prepared.reply, self.prepared.limited + " " + timestamp)
                            elif status == HANDLER_STATUS_COMMAND_ERROR:
                                self.__sp.publish(self.prepared.reply, self.prepared.command_error + " " + timestamp)
                            elif status == HANDLER_STATUS_PAYLOAD_ERROR:
                                self.__sp.publish(self.prepared.reply,
                                                  self.prepared.error + " " + value + " " + timestamp)
                            else:
                                raise Exception
                except:
                    self.__sp.publish(self.prepared.reply, "Internal Error " + timestamp)

                self.__exe_counter += 1
            else:
                pass

            if self.__exe_counter >= self.to_run.repetitions:
                with self.__lock:
                    self.__running = False
            else:
                time.sleep(self.to_run.interval)

    def __get_running(self):
        with self.__lock:
            value = self.__running
        return value

    def __set_running(self, value):
        with self.__lock:
            self.__running = value
            self.__exe_counter = 0

    running = property(__get_running, __set_running)


class Device(threading.Thread):
    def __init__(self):
        super().__init__()
        self.__comport = ""
        self.__invent_number = "0"
        self.commands = []
        self.sp = None
        self.mqtt = None

        self.__main_lock = threading.Lock()
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
                    executor = Extensions.Executer(subpub=self.sp, main_lock=self.__main_lock)
                    # adding to the list
                    self.executions.append(executor)

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

            if data.matching:
                # matching, we handle the standard commands
                if data.command == "?":
                    self.sp.publish(data.reply + "/manufactorer", self.manufactorer)
                    self.sp.publish(data.reply + "/devicetype", self.devicetype)
                    self.sp.publish(data.reply + "/model", self.model)
                    self.sp.publish(data.reply + "/serialnumber", str(self.serialnumber))
                    self.sp.publish(data.reply + "/commands", str(self.commands))
                    raise Exception
                elif data.command == "echo?" or data.reply == "ping?":
                    self.sp.publish(data.reply, str(datetime.datetime.utcnow()))
                    raise Exception
            else:
                # accessnumber is not matching
                return
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
                return Data(topic=topic, command=command, reply=reply_topic, matching=matching)
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
        payload_json = "{}"
        try:
            try:
                payload = payload.decode("utf-8")
            except:
                pass
            try:
                payload = payload.strip(" ")
                if not (str(payload).startswith("{") and str(payload).endswith("}")):
                    raise
                payload_json = payload
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
                        json=payload_json)
        except:
            raise

    # ------------------------------------------------------------------------------------------------
    # RUNNING configuration
    # ------------------------------------------------------------------------------------------------
    def to_run(self, data):
        repetitions = 1
        interval = 2
        return Extensions.Data(
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
