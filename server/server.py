import sys
import socket
import time
import threading


def sendFile(filename, serversocket, clientaddress):
    print("in sendFile")
    timeout = 100 # in milliseconds
    window_size = 4
    seq_num = 0
    w_left = 0
    w_right = window_size-1
    timer = [None] * window_size
    sr_buffer = [None] * window_size
    global ack_received
    ack_received = False

    def resend_pkt():
        global ack_received
        print("ack_received = ", ack_received)
        while not ack_received:
            for i in range(min(len(timer), w_right+1)):
                print("unacked_time[", i, "] = ", time.time()*1000 - timer[i][0])#'''*1000 - timer[i][0]'''
                if time.time()*1000 - timer[i][0] > timeout:
                    left = w_left % window_size
                    index = (left + (timer[i][1]-w_left)) % window_size
                    print("send... seq_num =", timer[i][1])
                    serversocket.sendto(sr_buffer[index], (clientaddress))
                    timer[i][0] = time.time()*1000
        ack_received = False
            

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
        print("send... seq_num =", seq_num)
        serversocket.sendto(buffer, (clientaddress))
        sr_buffer[pkt] = buffer
        timer[pkt] = list((time.time() * 1000, seq_num))
        if sendlen < 512:
            file_end = True
            last_pkt = pkt
            break
        seq_num += 1

    if file_end:
        w_right = last_pkt

    while w_left <= w_right:
        print("wleft = ", w_left, "  w_right = ", w_right)
        resend_thread = threading.Thread(target=resend_pkt)
        resend_thread.start()

        (clientack, addr) = serversocket.recvfrom(5)
        opcode = int(clientack[0:1])
        ack_seq = int.from_bytes(clientack[1:5], 'big')
        ack_received = True
        resend_thread.join()
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
                print("send... seq_num =", seq_num)
                serversocket.sendto(buffer, (clientaddress))
                left = w_left % window_size
                index = (left + (seq_num-w_left)) % window_size
                timer[index] = list((time.time()*1000, seq_num))
                sr_buffer[index] = buffer
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
print("received connect packet")
print(len(clientdata))
# print(clientaddress)
# print(clientdata, len(clientdata))

# sendFile("test.txt", serversocket, clientaddress)
sendFile("test.txt", serversocket, clientaddress)
serversocket.close()