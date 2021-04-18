import socket

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

import XSFTP




serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

serversocket.bind(("localhost", 10000))

print("Server started at %s; listening at port %d;" % (serversocket.getsockname()))

filename, acceptparams = XSFTP.accept(serversocket)
if not filename:
    print("accept error..")
    exit()

XSFTP.sendFile(filename, serversocket, acceptparams)

serversocket.close()