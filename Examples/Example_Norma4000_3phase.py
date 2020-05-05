import socket
import time
# basic code for SCPI communication with NORMA 4000Poweranalyzer
# be sure to make proper IP-settings and use
# it here

port        = 23                #telnet
ip          = b'192.168.0.111'  #ip address
buffersize  = 4096              #buffer size recommended = 4096

try:
    # create an ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect to the client
    client.connect((ip, port))

    # send RESET request
    # client.send(b'*RST\n')
    # time.sleep(2) #give 2 seconds to execute command
    # send Device Identification Request
    client.send(b'*IDN?\n')
    response = client.recv(buffersize)
    print (response)
    # send FUNC to measure all AC phase voltages
    client.send(b'FUNC "VOLT1:AC", "VOLT2:AC", "VOLT3:AC"\n')
    client.send(b'DATA?\n')
    # receive the response data
    response = client.recv(buffersize)
    voltAC123 = response.split(b',');
    voltAC1 = (float)(voltAC123 [0])
    voltAC2 = (float)(voltAC123 [1])
    voltAC3 = (float)(voltAC123 [2])
    voltAC1 = voltAC1 + 5.6 # any dummy calc
    voltAC2 = voltAC2 + 3.1 # any dummy calc
    print (voltAC1,voltAC2,voltAC3)
finally:
    # close the client
    client.close()
    print ("+++ end +++")
