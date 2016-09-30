import os,time
import hashlib
import threading
import atexit
import pickle

config = ".lansync"

Myfiles_enum = {}
Myfiles_meta = {}

NetFiles = []
uplist = []
downlist = []
processing_ignorelist = []


def scandir(directory):
    lst = os.listdir(directory)
    files_dic = {}
    for fle in lst:
        finfo = os.stat(directory+"/" +fle)
        cf = (0,finfo[6],finfo[9])
        files_dic[fle] = cf
    return files_dic

def GetEmmdie(filename):
    #Function sponsored By MD O'Shea Ballincollig
    md5 = hashlib.md5()
    with open(filename,'rb') as f: 
        for chunk in iter(lambda: f.read(8192), b''): 
            md5.update(chunk)
    return md5.digest()


    

class Dirwatcher(threading.Thread):
    
    def local_file_added(self,filename):
        if(filename in processing_ignorelist): return
        print("Added: " + filename)
        self.MyFiles[filename] = int(time.time())
        
    def local_file_changed(self,filename):
        if(filename in processing_ignorelist): return
        print("Changed: " + filename)
        self.MyFiles[filename] = int(time.time())

    def local_file_deleted(self,filename):
        if(filename in processing_ignorelist): return
        print("Deleted: " + filename)
        if(filename in self.MyFiles): del(self.MyFiles[filename])

    
    #Format (MyFiles,Netfiles,md)
    def loadconfig(self):
        if(os.path.isfile(config)):
            fl = open(config,'rb')
            (self.MyFiles,NetFiles) = pickle.load(fl)
            print("Directory config loaded from file...")
            fl.close()

    def saveconfig(self):
        fl = open(config,'wb')
        ts = (self.MyFiles,NetFiles)
        pickle.dump(ts,fl)
        fl.close()
        print("Directory config saved to file...")
            
    def __init__(self,path,freq):
        threading.Thread.__init__(self)
        self.MyFiles = {}
        self.path = path
        #MD - keep track of modified files
        self.md = scandir(self.path)
        self.freq = freq
        self.gone = []
        self.loadconfig()
        self.FirstRun = True
        
        
    def run(self):
        while 1:
            time.sleep(self.freq)
            sd = scandir(self.path)

            for fle in sd:
                #New file found
                if( ((fle in self.md) == False) and ((fle in self.MyFiles) == False) ):
                    self.local_file_added(fle)
                    finfo = os.stat(self.path+ "/" + fle)
                    cf = (0,finfo[6],finfo[9])
                    self.md[fle] = cf 
                #File modified
                if (fle in self.md) == True:
                    if(sd[fle] != self.md[fle]):
                        self.md[fle] = sd[fle]
                        self.local_file_changed(fle)        
            #File removed
            for fle in self.md:
                if(fle in sd) == False:
                    self.gone.append(fle)
                    self.local_file_deleted(fle)

            for a in self.gone:
                del(self.md[a])
            self.gone = []

            if(self.FirstRun):
                self.FirstRun = False
                self.saveconfig()

            
#atexit.register(dwo.saveconfig)
