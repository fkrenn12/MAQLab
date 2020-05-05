import socket
import time
# basic code for SCPI communication with NORMA 4000Poweranalyzer
# be sure to make proper IP-settings and use
# it here

port        = 23                #telnet
ip          = b'172.16.65.32'   #ip address  POWER ANALYZER #498
buffersize  = 4096              #buffer size recommended = 4096

try:
    # create an ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect to the client
    client.connect((ip, port))

    # send RESET request / commented becaus 
    # client.send(b'*RST\n')
    # time.sleep(2) #give 2 seconds to execute command
    # send Device Identification Request
    client.send(b'*IDN?\n')
    response = client.recv(buffersize)
    print (response)
    # send FUNC to measure AC phase voltage 1
    client.send(b'FUNC "VOLT1:AC"\n') #this command sets whats to measure
    client.send(b'DATA?\n')           #this command gets the measured value
    # receive the response data
    response = client.recv(buffersize)
    voltAC1 = (float)(response)
    voltAC1 = voltAC1 + 0.00 # any dummy calc
    print (voltAC1)
finally:
    # close the client
    client.close()
    print ("+++ end +++")
