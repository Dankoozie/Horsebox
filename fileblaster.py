import dw
import hashlib
import threading
import time
import sqlite3
import uuid

from socket import *
from struct import *
from os.path import getsize
from math import ceil
from random import randint

CHUNK_SIZE = 32768
BC_MAX_SIZE = 32768*32

#Active file transfers
Incoming = {}
Outgoing = {}

#Set up socket stuff
sock = socket(AF_INET6, SOCK_DGRAM)
bcast_addr = "ff02::1"
bcast_port = 54779
listen_port = 54779
sock.bind(('',listen_port))
listen_running = True

#Network stuff general
announce_freq = 19


#Change buffer size
print(sock.getsockopt(SOL_SOCKET,SO_RCVBUF))
sock.setsockopt(SOL_SOCKET,SO_RCVBUF,1024*1024)
print(sock.getsockopt(SOL_SOCKET,SO_RCVBUF))



OutPackets = []


#DB Setup
sqdb = sqlite3.connect('horsebox.db')
c = sqdb.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS Myfiles  (fid int PRIMARY KEY, fname text UNIQUE, md5 text, size int, ctime int, mtime int, atime int)''')
c.execute('''CREATE TABLE IF NOT EXISTS Peers  (uuid text PRIMARY KEY,friendlyname text, lastlocal_ip text,lastseen int, sharedkey text )''')
c.execute('''CREATE TABLE IF NOT EXISTS Peerfiles  (text, bnum text, starttime int, duration real, cents real, wcc text, year int, month int)''')

class MyUser():
    def __init__(self):
        self.uuid = uuid.uuid4().bytes
        self.MyFriendlyName = bytes('Sh1tbag','utf-8')
        self.guid = 4



    

def SendToc(folder,addr):
    a = dw.scandir(folder)
    print(a)
    for f in a:
        a[f] = (a[f][0],a[f][1],a[f][2], dw.GetEmmdie('Shared/' + f))
        print(a[f])
        

def BAnnounce(fname,ftid,size,chunk_count,enc = None):
    #Announce a new / changed file on the network
    OutPackets.insert(0,(bytes('a','ascii') + pack('QQII',ftid,size,CHUNK_SIZE,chunk_count) + bytes(fname,'utf-8'),(bcast_addr,bcast_port)))


def Packetchunk(chunk,ftid, enc= None):
    #Take a chunk and put into packet format ready for sending
    phead = pack("IQQ",ftid,chunk[0],chunk[1])
    return bytes('q','ascii') + phead + chunk[2]


class FileO():
    #Outgoing file transfer object
    def __init__(self,path):
        self.path = path
        self.name = self.path[self.path.rfind('/'):]
        self.size = getsize(path)
        self.bid = randint(1,65000)

        self.mdOShea = hashlib.md5()

        #Resend
        self.rebroadcast = []
        self.last_request = 0
        self.Destroytimeout = 0
        

    def Chunklist(self):
        return range(0,ceil(self.size / CHUNK_SIZE))

    def Chunks(self):
        fz = open(self.path,'rb')
        stp = self.Chunklist().stop -1
        for i in self.Chunklist():
            fz.seek((i)*CHUNK_SIZE)
            Cur = fz.read(CHUNK_SIZE)
            yield((stp,i,Cur))

    def CertainChunks(self,clist):
        fz = open(self.path,'rb')
        stp = self.Chunklist().stop -1
        for i in clist:
            fz.seek((i)*CHUNK_SIZE)
            Cur = fz.read(CHUNK_SIZE)
            yield((stp,i,Cur))

    def Blast(self):
        #Broadcast entire file over network
        BAnnounce(self.path,self.bid,self.size,self.Chunklist().stop -1)
        time.sleep(0.01)
        for a in self.Chunks():
            time.sleep(0.1)
            OutPackets.insert(0,(Packetchunk(a,self.bid,self.size),(bcast_addr,bcast_port)))

    def SendIndividual(self,addr):
        #Send file to one client
        pass
    

    def Rebroadcast(self):
        pass

class FileI():
    #Incoming file transfer object
    def __init__(self,fid,cs,cn):
        self.chunk_size = cs
        self.name = ''
        self.path = ''
        self.sender = ''
        self.ip = ''
        #Packet transfer stuff
        self.passcount = 0
        self.dupecount = 0
        self.lastvalid_received = 0
        self.time_between_received = 0
        
        self.size = 0
        self.chunks = {}
        self.chunk_num = cn
        self.complete = False
        self.missing = list(range(cn + 1))
        self.Destroytimeout = 0
        self.EmmdieFive = hashlib.md5()
        self.compfile = b''
        self.wrotefile = False
    def iscomplete(self):
        for i in range(self.chunk_num):
            if(not i in self.chunks):
                return False

        self.complete = True
        return True

    def addchunk(self,cn,cd):
        self.chunks[cn] = cd
        if(cn in self.missing): self.missing.remove(cn)
        else: print("Not found: ", cn)
        self.iscomplete()
        
    def cr(self):
        print(self.chunks.keys())
        print(self.chunk_num)

    def reassemble(self):
        if(self.complete == False): return False
        for a in range(self.chunk_num + 1):
            self.EmmdieFive.update(self.chunks[a])
            #print("Reassembling chunk ", str(a), "of length ", str(len(self.chunks[a]))) 
            self.compfile = self.compfile + self.chunks[a]
        if(not self.wrotefile):
            of = open('temporary_outfile.jpg','wb')
            of.seek(0)
            of.write(self.compfile)
            of.close()
            self.wrotefile = True
            print("File writtn, md5: ", str(self.EmmdieFive.hexdigest()))



def Process_announce(addr,data):
    ftid,size,CS,cn = unpack('QQII',data[1:25])
    name = data[25:529]
    print(size, name, ftid, addr,CS,cn)
    if(not ftid in Incoming):
        fi = FileI(ftid,CS,cn)
        fi.size = size
        fi.name = name
        fi.sender = addr

        Incoming[ftid] = fi

def Process_chunk(addr,data):
    hdr = unpack("IQQ",data[1:25])
    if(hdr[0] in Incoming):
        Incoming[hdr[0]].addchunk(hdr[2],data[25:])
        #print("Chunk ", str(hdr[2]), " arrived with size ", len(data[25:]))
    else:
        print("Chunk received for uninitiated transfer")

def Process_missing(addr,data):
    hdr = unpack("I",data[:4])
    if(hdr[0] in Outgoing):
        print("Hai")

def Process_hai(addr,data):
    print("Peer discovered: " + str(data[1:],'utf-8'))

def ProcessIncoming(addr,data):
    print("WHIP")
    if(data[0] == 97): Process_announce(addr,data)
    elif(data[0] == 113): Process_chunk(addr,data)
    elif(data[0] == 104): Process_hai(addr,data)
    else:
        print(data[0])
    
def Shout():
    #print("Shouting!")
    OutPackets.insert(0,(b'h'+Mu.MyFriendlyName,(bcast_addr,bcast_port)))

class sendpackets(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.atimer = announce_freq
        
    def run(self):

        while(1):
            if(len(OutPackets) > 0):
                #print("OutPackets: " + str(len(OutPackets)))
                pck = OutPackets.pop()
                sock.sendto(pck[0],pck[1])                
            else:
                time.sleep(0.2)
                self.atimer -= 0.2
                if(self.atimer < 0):
                    Shout()
                    self.atimer = announce_freq
                    

class listen(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.recvd = 0
    def run(self):
        while listen_running:
            data, addr = sock.recvfrom(70000)
            #logging.debug("LAN: Received packet of length " + str(len(data)) + " from: " + addr[0] + ":" + str(addr[1]))
            ProcessIncoming(addr, data)
                          

class DirHoor(dw.Dirwatcher):
    def __init__(self):
        dw.Dirwatcher.__init__(self,'Shared',1)
    def local_file_changed(self,filename):
        print("A load of shite!: " + filename)

Mu = MyUser()
print(Mu.uuid)


listener = listen()
listener.start()
sender = sendpackets()
sender.start()

hg = DirHoor()
hg.start()

SendToc('Shared','wun-nine-too')

#F = FileO('20160820_016.jpg')
#print(F.name) 0868805980
#F.Blast() 0.15
#This line of code was sponsored by: Crafted Fitted Furniture Ltd 6 Bridge Street, Mallow, Co.Cork 
