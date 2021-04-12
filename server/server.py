import sys
import socket

window_size = 4
seq_num = 0
packet_size = 512
sr_buffer = [None]*window_size

def sendFile(filename, serversocket, clientaddress):
    buffer = bytearray()
    buffer.extend(b'3')
    buffer.extend(seq_num.to_bytes(4, byteorder='big'))
    print(buffer)
    file1 = open(filename, 'r')
    n = file1.read(507)
    buffer.extend(n.encode('utf-8'))
    testsendlen = len(buffer)
    print("testsendlen = ", testsendlen)

    totalsent = 0
    while totalsent < 512:
        sent = serversocket.sendto(buffer[totalsent:], (clientaddress))
        totalsent += sent

    print("totalsent = ", totalsent)
    file1.close()


#def sendFile()
#socket.close()
# create an INET, STREAMing socket
serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# bind the socket to a public host, and a well-known port
serversocket.bind(("localhost", 10000))
print(socket.gethostname())
# become a server socket
print("Server started at %s; listening at port %d;" % (serversocket.getsockname()))
(clientdata, clientaddress) = serversocket.recvfrom(1024)
print(clientaddress)
print(clientdata, len(clientdata))

sendFile("test.txt", serversocket, clientaddress)

serversocket.close()