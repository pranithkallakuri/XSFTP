import sys
import socket

def sendFile(filename, serversocket, clientaddress):
    print("in sendFile")
    window_size = 4
    seq_num = 0
    w_left = 0
    w_right = window_size-1

    file1 = open(filename, 'r')
    file_end = False
    last_pkt = -1
    for pkt in range(window_size):
        buffer = bytearray()
        buffer.extend(b'3')
        buffer.extend(seq_num.to_bytes(4, byteorder='big'))
        n = file1.read(507)
        buffer.extend(n.encode('utf-8'))
        sendlen = len(buffer)
        print("sendlen = ", sendlen)
        print("buffer >>", buffer)
        serversocket.sendto(buffer, (clientaddress))
        if sendlen < 512:
            file_end = True
            last_pkt = pkt
            break
        seq_num += 1

    if file_end:
        w_right = last_pkt

    while w_left <= w_right:
        print("wleft = ", w_left, "  w_right = ", w_right)
        (clientack, addr) = serversocket.recvfrom(5)
        opcode = int(clientack[0:1])
        ack_seq = int.from_bytes(clientack[1:5], 'big')
        if opcode != 4 or (ack_seq < w_left or ack_seq > w_right):
            continue
        if ack_seq == w_left:
            w_left += 1
            if not file_end:
                w_right += 1
                buffer = bytearray()
                buffer.extend(b'3')
                buffer.extend(seq_num.to_bytes(4, byteorder='big'))
                n = file1.read(507)
                buffer.extend(n.encode('utf-8'))
                sendlen = len(buffer)
                print("sendlen = ", sendlen)
                print("buffer >>", buffer)
                serversocket.sendto(buffer, (clientaddress))
                if sendlen < 512:
                    file_end = True
                seq_num += 1

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
(clientdata, clientaddress) = serversocket.recvfrom(2048)
print(len(clientdata))
# print(clientaddress)
# print(clientdata, len(clientdata))

# sendFile("test.txt", serversocket, clientaddress)
sendFile("test.txt", serversocket, clientaddress)
serversocket.close()