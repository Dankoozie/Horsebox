from netifaces import *
#94.5.43.240
#0874474321
lsn = interfaces()


def getaddrs(adic):
    rt = []
    for a in adic:
        if('addr' in a): rt.append(a['addr'])
    return rt

def getfe80s():
    al = []
    for a in lsn:
        adr_l = ifaddresses(a)
        if(AF_INET6 in adr_l): al.append((a,adr_l[AF_INET6]))

    for a in al:
        return(a[0],getaddrs(a[1]))



getfe80s()
