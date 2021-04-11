import socket

#socket.close()
# create an INET, STREAMing socket
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# bind the socket to a public host, and a well-known port
serversocket.bind((socket.gethostname(), 10000))
print(socket.gethostname())
# become a server socket
serversocket.listen(5)

serversocket.accept()
serversocket.close()