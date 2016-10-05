from netifaces import *
#94.5.43.240
#0874474321
lsn = interfaces()

def getfe80s():
    fe80dic = {}
    for a in lsn:
        adr_l = ifaddresses(a)
        if(AF_INET6 in adr_l): print(a, adr_l[10])


getfe80s()
