import socket

#def recvFile(sock):


# create an INET, STREAMing socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# now connect to the web server on port 80 - the normal http port
sock.sendto("Hello".encode('utf-8'), ('localhost', 10000))

# recvFile() (receives data packets (client))
# sendFile() (sends data packets (server))

k = sock.recvfrom(512)
#print(k[0].decode('utf-8'))
print(k[0])
#connect(filename, ip, port)