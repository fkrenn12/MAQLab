import datetime
import shared as s


# --------------------------------------------------------
#  V A L I D A T E  incoming  P A Y L O A D
# --------------------------------------------------------
def validate_payload(payload):
    timestamp = str(datetime.datetime.utcnow())
    payload_error = s.payload_error + " " + timestamp
    payload_accepted = s.payload_accepted + " " + timestamp
    payload_limited = s.payload_limited + " " + timestamp
    payload_command_error = s.payload_command_error + " " + timestamp
    try:
        payload = payload.lower()
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        if not isinstance(payload, str):
            payload = str(payload)
        if payload == "":
            payload = "0"
        payload = payload.replace('off', "0")
        payload = payload.replace("on", "1")
        try:
            payload = float(payload)
        except:
            raise
    except:
        raise
    return {'payload': payload,
            'payload_error': payload_error,
            'payload_accepted': payload_accepted,
            'payload_command_error': payload_command_error,
            'payload_limited': payload_limited}


# --------------------------------------------------------
#  V A L I D A T E  incoming  T O P I C
# --------------------------------------------------------
def validate_topic(topic, serial_number, model):
    command = ""
    matching = False
    reply_topic = ""
    try:
        topic = topic.decode("utf-8")
    except:
        pass

    try:
        topic = topic.lower()
        topic_splitted = topic.split("/")
    except:
        raise

    split_count = len(topic_splitted)
    if 3 <= split_count < 7 and topic_splitted[0] == s.topic_root:
        try:
            index_of_cmd = topic_splitted.index(s.topic_cmd)
            reply_topic = topic.replace(s.topic_cmd, s.topic_reply)
            if topic_splitted[index_of_cmd + 1] == s.topic_request:
                command = s.topic_access_number
                reply_topic = reply_topic.replace(s.topic_request, "")
                reply_topic = reply_topic + model + "/" + s.topic_access_number
            else:
                command = topic_splitted[index_of_cmd + 2]
                command = command.replace("1", "")
                command = command.replace(" ", "")
                if topic_splitted[index_of_cmd + 1] == str(serial_number):
                    matching = True
            return {"topic": topic, 'cmd': command, 'matching': matching, 'reply': reply_topic}
        except:
            raise
    raise Exception