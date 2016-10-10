from netifaces import *
#94.5.43.240
#0874474321
lsn = interfaces()


def getaddrs(adic,filt = 'fe80:'):
    rt = []
    for a in adic:
        if('addr' in a):
            if(a['addr'][:len(filt)] == filt): rt.append(a['addr'])
    return rt

def getfe80s():
    #Get all interfaces and link-local addresses
    fe80 = []
    al = []
    for a in lsn:
        adr_l = ifaddresses(a)
        if(AF_INET6 in adr_l): al.append((a,adr_l[AF_INET6]))

    for a in al:
        fh = getaddrs(a[1],'fe80:')
        if(fh): yield((a[0],getaddrs(a[1])))
        


