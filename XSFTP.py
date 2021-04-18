import os
import socket
import time
import threading
import random

errorcodes = {
    0 : "NotDefined",
    1 : "FileNotFound",
    2 : "RequestrejectedByServer",
    3 : "Access Violation",
    4 : "IncorrectlyFormedPacket"
}

def connect(sock, filename, serveraddress, connect_timeout=1):
    #connect_timeout = 1 #in seconds

    oldtimeout = sock.gettimeout()
    
    buffer = bytearray()
    buffer.extend(b'1')
    if len(filename) > 510:
        print("Filename too long")
        return None
    buffer.extend(filename.encode('utf-8'))
    buffer.extend(b'\0')

    recvdata = None
    seq_num = None
    recv_window = None
    print("connecting...")
    while True:
        sock.settimeout(connect_timeout)
        sent = sock.sendto(buffer, serveraddress)
        try:
            recvdata, addr = sock.recvfrom(9)
            if not recvdata:
                return None
            opcode = int(recvdata[0:1])
            #print("opcode = ", opcode)
            if opcode == 5:
                err = int.from_bytes(recvdata[1:5], 'big')
                print("ErrorFromServer:", errorcodes[err])
                return None

            if opcode == 2:
                #Get data
                seq_num = int.from_bytes(recvdata[1:5], 'big')
                recv_window = int.from_bytes(recvdata[5:9], 'big')
                #send ack
                ack = bytearray()
                ack.extend(b'4')
                ack.extend(seq_num.to_bytes(4, byteorder='big'))
                sent = sock.sendto(ack, serveraddress)
                sock.settimeout(oldtimeout)
                ackackdata, addr = sock.recvfrom(512)
                opcode = int(ackackdata[0:1])
                if opcode == 3:
                    break
                elif opcode == 5:
                    err = int.from_bytes(ackackdata[1:5], 'big')
                    print("ErrorFromServer:", errorcodes[err])
                    return None
                else:
                    print("Server sent incorrect response. Resending request...")
        except socket.timeout:
            print("Connect request timed out / was lost /" + 
                    "Server did not respond. Resending request...")
    
    sock.settimeout(oldtimeout)
    print("Connected to Server!")
    return seq_num, recv_window



def recvFile(sock, filename, serveraddress, socket_timeout=5):
    #socket_timeout = 5 # in seconds
    #print("in recvFile")
    sock.settimeout(socket_timeout)

    connect_data = connect(sock, filename, serveraddress)
    if connect_data == None:
        print("connect error...")
        return

    window_size = connect_data[1]
    sr_buffer = [None]*window_size
    w_left = 0
    w_right = window_size-1
    acked_packet = [False] * window_size

    file1 = open(filename, 'wb')
    recv_ended = False

    while True:
        #print("received packet..")
        # if recv_ended:
        #     print("Client will timeout in 5 seconds")
        try:
            (recvdata, addr) = sock.recvfrom(512)
        except socket.timeout:
            if recv_ended:
                print("File received succesfully")
            else:
                print("Socket Timed out")
                print("Incomplete file written")
            break
        #print("recvdata = ", recvdata)
        if not recvdata:
            print("Incorrect data received")
            continue
            #return

        #print("Data received from server = ", recvdata)

        seq_num = int.from_bytes(recvdata[1:5], 'big')
        opcode = int(recvdata[0:1])
        #print("opcode = ", opcode, "  seq_num = ", seq_num)
        print("w_left = ", w_left, "  w_right = ", w_right)
        if opcode != 3 or seq_num > w_right:
            #print("seq_num too big")
            continue
            #return
        left = w_left % window_size
        index = (left + (seq_num-w_left)) % window_size
        if sr_buffer[index] == None and seq_num >= w_left:
            sr_buffer[index] = recvdata
            acked_packet[index] = True

        ack = bytearray()
        ack.extend(b'4')
        ack.extend(seq_num.to_bytes(4, byteorder='big'))
        print("ack = ", ack, " | ", "len = ", len(ack), " | seq_num = ", seq_num)
        
        sock.sendto(ack, serveraddress)

        while acked_packet[left]:
            file1.write(sr_buffer[left][5:])
            #print("this is written into file = ", sr_buffer[left][5:])
            sr_buffer[left] = None
            acked_packet[left] = False
            w_left += 1
            w_right += 1
            left = w_left % window_size
        
        if len(recvdata) < 512 and recv_ended == False:
            print("Received packet < 512 in size")
            recv_ended = True

    print("Closing file...")
    file1.close()
    print("Done")


def accept(serversocket, window_size=20, accept_timeout=1):
    ##########--SERVERPARAMS--#############
    #seq_num = randint(1000, 2**30-1)
    #accept_timeout = 1 #in seconds
    #######################################
    oldtimeout = serversocket.gettimeout()
    print("Waiting for client...")
    clientreq = None
    clientaddress = None

    while True:
        serversocket.settimeout(None)
        clientreq, clientaddr = serversocket.recvfrom(512)
        
        if not clientreq or not clientaddr:
            print("None data received in accept")
            return None

        opcode = int(clientreq[0:1])
        filename = clientreq[1:-1].decode('utf-8')
        if opcode == 1:
            #Check if file exists
            if filename not in os.listdir('.'):
                buffer = bytearray()
                buffer.extend(b'5')
                err = 1
                buffer.extend(err.to_bytes(4, byteorder='big'))
                serversocket.sendto(buffer, (clientaddr))
                continue

            #Sending connection assign packet
            seq_num = random.randint(1000, 2**30-1)
            buffer = bytearray()
            buffer.extend(b'2')
            buffer.extend(seq_num.to_bytes(4, byteorder='big'))
            buffer.extend(window_size.to_bytes(4, byteorder='big'))
            serversocket.sendto(buffer, (clientaddr))

            #Now waiting for ack from client
            serversocket.settimeout(accept_timeout)
            try:
                clientack, addr = serversocket.recvfrom(5)
                opcode = int(clientack[0:1])
                ack_seq = int.from_bytes(clientack[1:5], 'big')
                if opcode == 4 and ack_seq == seq_num:
                    print("Received ack from client")
                    break
            except socket.timeout:
                print("Ack not received from client, waiting for new initial request")
                continue
            
    print("Flushing input buffer..")
    serversocket.settimeout(0.1)
    while True:
        try:
            trash = serversocket.recvfrom(1000)
        except socket.timeout:
            break
    
    #print("oldtimeout = ", oldtimeout)
    serversocket.settimeout(oldtimeout)
    print('Client found!')
    return (filename, (clientaddr, window_size))







def sendFile(filename, serversocket, acceptparams, disconnect_timeout=5, ack_timeout=250):
    #print("in sendFile")
    serversocket.settimeout(disconnect_timeout)
    ##########-ACK TIMEOUT-###########
    timeout = ack_timeout      # in milliseconds
    ########################################

    #print(acceptparams)
    window_size = acceptparams[1]
    seq_num = 0
    clientaddress = acceptparams[0]

    w_left = 0
    w_right = window_size-1
    timer = [None] * window_size
    sr_buffer = [None] * window_size
    ack_recv_n = [False] * window_size
    global ack_received
    ack_received = False
    file_end = False
    final_ack_seq = -1
    global daemon_returned
    daemon_returned = False

    # def resend_pkt():
    #     global ack_received
    #     print("ack_received = ", ack_received)
    #     while not ack_received:
    #         for i in range(min(len(timer), w_right+1)):
    #             print("unacked_time[", i, "] = ", time.time()*1000 - timer[i][0])#'''*1000 - timer[i][0]'''
    #             if time.time()*1000 - timer[i][0] > timeout:
    #                 left = w_left % window_size
    #                 index = (left + (timer[i][1]-w_left)) % window_size
    #                 print("send... seq_num =", timer[i][1])
    #                 serversocket.sendto(sr_buffer[index], (clientaddress))
    #                 timer[i][0] = time.time()*1000
    #     ack_received = False

    def ack_listen():
        global ack_received
        global daemon_returned
        while True:
            #print("Waiting for ack...")
            try:
                (clientack, addr) = serversocket.recvfrom(5)
            except socket.timeout:
                if w_left == w_right+1:
                    print("File sent successfully")
                    print("Closing connection...")
                else:
                    print("Client did not respond.. Sending error packet and closing connection.")
                    #Send error packet
                daemon_returned = True
                ack_received = True
                return
            opcode = int(clientack[0:1])
            ack_seq = int.from_bytes(clientack[1:5], 'big')
            #print("received ack with opcode, seq_num = ", opcode, ack_seq)
            left = w_left % window_size
            index = (left + (ack_seq-w_left)) % window_size
            if opcode != 4 or (ack_seq < w_left or ack_seq > w_right) or ack_recv_n[index]:
                #print("NOT making ack_true")
                continue
            #print("in_ack_listen ack_recv_n = ", ack_recv_n)
            ack_recv_n[index] = True
            ack_received = True
            #print("Made ack_true")
            

            

    file1 = open(filename, 'r')
    last_pkt = -1
    for pkt in range(window_size):
        buffer = bytearray()
        buffer.extend(b'3')
        buffer.extend(seq_num.to_bytes(4, byteorder='big'))
        n = file1.read(507)
        buffer.extend(n.encode('utf-8'))
        sendlen = len(buffer)
        # print("sendlen = ", sendlen)
        # print("buffer >>", buffer)
        #print("send... seq_num =", seq_num)
        serversocket.sendto(buffer, (clientaddress))
        sr_buffer[pkt] = buffer
        timer[pkt] = list((time.time() * 1000, seq_num))
        ack_recv_n[pkt] = False
        if sendlen < 512:
            print("Sent last packet!")
            file_end = True
            last_pkt = pkt
            final_ack_seq = seq_num
            break
        seq_num += 1

    if file_end:
        w_right = last_pkt

    listen_daemon = threading.Thread(target=ack_listen)
    listen_daemon.start()
    while w_left <= w_right:
        print("wleft = ", w_left, "  w_right = ", w_right)
        # resend_thread = threading.Thread(target=resend_pkt)
        # resend_thread.start()
        # resend_thread.join()
        
        #print("ack_received = ", ack_received)
        #time.sleep(0.5)
        while not ack_received:
            #print("ack_received = ", ack_received)
            for i in range(min(len(timer), w_right+1)):
                #print("unacked_time[", i, "] = ", time.time()*1000 - timer[i][0])#'''*1000 - timer[i][0]'''
                left = w_left % window_size
                index = (left + (timer[i][1]-w_left)) % window_size
                if time.time()*1000 - timer[i][0] > timeout and not ack_recv_n[index]:
                    print("resend... seq_num =", timer[i][1])
                    serversocket.sendto(sr_buffer[index], (clientaddress))
                    timer[i][0] = time.time()*1000
        ack_received = False


        # ack_received = True
        left = w_left % window_size
        #print("ack_recv_n[left] = ", ack_recv_n[left])
        while ack_recv_n[left]:
            #print("in send next loop")
            ack_recv_n[left] = False
            #time.sleep(0.5)
            w_left += 1
            left = w_left % window_size
            #print("left = ", left)
            #print("ack_recv_n = ", ack_recv_n)
            if not file_end:
                w_right += 1
                buffer = bytearray()
                buffer.extend(b'3')
                buffer.extend(seq_num.to_bytes(4, byteorder='big'))
                n = file1.read(507)
                buffer.extend(n.encode('utf-8'))
                sendlen = len(buffer)
                # print("sendlen = ", sendlen)
                # print("buffer >>", buffer)
                #print("send... seq_num =", seq_num)
                serversocket.sendto(buffer, (clientaddress))
                # left = w_left % window_size
                index = (left + (seq_num-w_left)) % window_size
                timer[index] = list((time.time()*1000, seq_num))
                sr_buffer[index] = buffer
                ack_recv_n[index] = False
                if sendlen < 512:
                    print("Sent last packet!")
                    final_ack_seq = seq_num
                    file_end = True
                seq_num += 1
            

    #print("Reached before join")
    listen_daemon.join()
    #print("do you even get here")
    if final_ack_seq == -1:
        print("Lost connection to client... Incomplete send... Sending error packet...")
        # Send error packet

    file1.close()

