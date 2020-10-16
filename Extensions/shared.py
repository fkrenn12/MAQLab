import datetime


# --------------------------------------------------------
#  V A L I D A T E  incoming  P A Y L O A D
# --------------------------------------------------------
def validate_payload(payload):
    timestamp = str(datetime.datetime.utcnow())
    payload_error = "ERROR " + timestamp
    payload_accepted = "ACCEPTED " + timestamp
    valid = True
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
            valid = False
    except:
        valid = False
    return {"valid": valid, 'payload': payload, 'payload_error': payload_error, 'payload_accepted': payload_accepted}


# --------------------------------------------------------
#  V A L I D A T E  incoming  T O P I C
# --------------------------------------------------------
def validate_topic(topic, serial_number, model):
    command = ""
    matching = False
    reply_topic = ""

    if isinstance(topic, bytes):
        topic = topic.decode("utf-8")
    if isinstance(topic, str):
        topic = topic.lower()
        topic_splitted = topic.split("/")
        split_count = len(topic_splitted)
        if 3 <= split_count < 6 and topic_splitted[0] == "maqlab":
            try:
                index_of_cmd = topic_splitted.index("cmd")
            except:
                return {'valid': False}
            reply_topic = topic.replace("cmd", "rep")
            if topic_splitted[index_of_cmd + 1] == "?":
                command = "accessnumber"
                reply_topic = reply_topic.replace("?", "")
                reply_topic = reply_topic + model + "/accessnumber"
            else:
                command = topic_splitted[index_of_cmd + 2]
                command = command.replace("1", "")
                command = command.replace(" ", "")
                if topic_splitted[index_of_cmd + 1] == str(serial_number):
                    matching = True

            return {'valid': True, "topic": topic, 'cmd': command, 'matching': matching, 'reply': reply_topic}

    return {'valid': False}
