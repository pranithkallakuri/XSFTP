import socket
import time

errorcodes = {
    0 : "NotDefined",
    1 : "FileNotFound",
    2 : "RequestrejectedByServer",
    3 : "Access Violation",
    4 : "IncorrectlyFormedPacket"
}

def connect(sock, filename, serveraddress):
    connect_timeout = 1


    oldtimeout = sock.gettimeout()
    sock.settimeout(connect_timeout)
    
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
        sent = sock.sendto(buffer, serveraddress)
        try:
            recvdata, addr = sock.recvfrom(9)
            if not recvdata:
                return None
            opcode = int(recvdata[0:1])
            print("opcode = ", opcode)
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
                ackackdata, addr = sock.recvfrom(512)
                opcode = int(ackackdata[0:1])
                if opcode == 3:
                    break
                else:
                    continue
        except socket.timeout:
            print("Connect request timed out / was lost. Resending request...")
    
    sock.settimeout(oldtimeout)
    print("Connected to Server!")
    return seq_num, recv_window


def recvFile(sock, filename, serveraddress):
    socket_timeout = 5 # in seconds
    print("in recvFile")
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
        print("received packet..")
        # if recv_ended:
        #     print("Client will timeout in 5 seconds")
        try:
            (recvdata, addr) = sock.recvfrom(512)
        except socket.timeout:
            print("File received succesfully")
            print("Socket Timed out")
            break
        #print("recvdata = ", recvdata)
        if not recvdata:
            print("Incorrect data received")
            continue
            #return

        print("Data received from server = ", recvdata)

        seq_num = int.from_bytes(recvdata[1:5], 'big')
        opcode = int(recvdata[0:1])
        print("opcode = ", opcode, "  seq_num = ", seq_num)
        print("w_left = ", w_left, "  w_right = ", w_right)
        if opcode != 3 or seq_num > w_right:
            print("seq_num too big")
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
            print("this is written into file = ", sr_buffer[left][5:])
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
        
    
    
    
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serveraddress = ('localhost', 10000)

#sock.sendto(str2.encode('utf-8'), serveraddress)

# recvFile() (receives data packets (client))
# sendFile() (sends data packets (server))

recvFile(sock, "test.txt", serveraddress)

sock.close()
#print(k[0].decode('utf-8'))
#print(k[0])
#connect(filename, ip, port)