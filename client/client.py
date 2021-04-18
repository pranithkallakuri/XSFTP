import socket
import time

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

import XSFTP
    
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

serveraddress = ('localhost', 10000)

XSFTP.recvFile(sock, "other.c", serveraddress)

sock.close()
