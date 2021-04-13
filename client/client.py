import socket

def recvFile(sock, filename, serveraddress):
    print("in recvFile")
    window_size = 4
    # flag = connect()
    # if flag == 0 return None
    sr_buffer = [None]*window_size
    w_left = 0
    w_right = window_size-1

    file1 = open(filename, 'wb')

    while True:
        (recvdata, addr) = sock.recvfrom(512)
        if not recvdata:
            #Do not send ack
            continue
            #return

        seq_num = int.from_bytes(recvdata[1:5], 'big')
        opcode = int(recvdata[0:1])
        print("opcode = ", opcode, "  seq_num = ", seq_num)
        if opcode != 3 or seq_num > w_right:
            #do not send ack
            continue
            #return
        left = w_left % window_size
        index = (left + (seq_num-w_left)) % window_size
        if sr_buffer[index] == None and seq_num >= w_left:
            sr_buffer[index] = recvdata

        ack = bytearray()
        ack.extend(b'4')
        ack.extend(seq_num.to_bytes(4, byteorder='big'))
        print("ack = ", ack, " | ", "len = ", len(ack), " | seq_num = ", seq_num)
        
        sock.sendto(ack, serveraddress)

        if seq_num == w_left:
            file1.write(sr_buffer[left][5:])
            sr_buffer[left] = None
            w_left += 1
            w_right += 1
        
        if len(recvdata) < 512:
            print("Received packet < 512 in size")
            file1.close()
            return

    file1.close()
        
    
    
    
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serveraddress = ('localhost', 10000)
# now connect to the web server on port 80 - the normal http port
str1 = """
hellohellohellohellohellohellohellohellohellohello
hellohellohellohellohellohellohellohellohellohello
hellohellohellohellohellohellohellohellohellohello
hellohellohellohellohellohellohellohellohellohello
hellohellohellohellohellohellohellohellohellohello
hellohellohellohellohellohellohellohellohellohello
hellohellohellohellohellohellohellohellohellohello
hellohellohellohellohellohellohellohellohellohello
hellohellohellohellohellohellohellohellohellohello
hellohellohellohellohellohellohellohellohellohello
hello
"""
# str2 = """
# byebyebyebyebyebyebyebyebyebyebyebyebye
# byebyebyebyebyebyebyebyebyebyebyebyebye
# byebyebyebyebyebyebyebyebyebyebyebyebye
# byebyebyebyebyebyebyebyebyebyebyebyebyebye
# """
sent = sock.sendto(str1.encode('utf-8'), serveraddress)
print(sent)
#sock.sendto(str2.encode('utf-8'), serveraddress)

# recvFile() (receives data packets (client))
# sendFile() (sends data packets (server))

recvFile(sock, "recv.txt", serveraddress)

sock.close()
#print(k[0].decode('utf-8'))
#print(k[0])
#connect(filename, ip, port)