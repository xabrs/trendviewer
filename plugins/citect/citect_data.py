import ctypes as c
from struct import unpack, calcsize
from datetime import datetime, timedelta
import os

VERSION_FIELD_POS = 0x8A
FORMAT6 = "<112sffff8shh20x64s8x2xliiil8siQQiiq6x"
HEADER6SIZE = calcsize(FORMAT6)

FORMAT5 = "<112sffff8shh4x64s8x2xliiil8siiiiii6x"
HEADER5SIZE = calcsize(FORMAT5)
def date1601(d):
    return datetime(1601, 1, 1, 0, 0, 0) + timedelta(seconds = d/1e7)
def date1900(d):
    return datetime(1970, 1, 1, 0, 0, 0) + timedelta(seconds = d)

class header(object):
    """TwoByteOriginal, TwoBytePreV500, TwoByteV500, TwoByteV531"""
    Title = b"",          #ASCII title of the file. It contains information, such as, file version, type, start time and logging name.
    RawZero = 0.0,  
    RawFull = 0.0,  
    EngZero = 0.0,  
    EngFull = 0.0,  
    ID = b"",             #ID for Citect files. It is set to "CITECT".
    FileType = 0,         #Type of the Citect file. It is set to 0, which is FILE_TYPE_TREND.
    Version = 0,          #Version number of the trends. (equal to 3 for this Storage Method)
    LogName = b"",        #Name of the trend record that owns the history file.
    Mode = 0              #Indicates the mode of the history file. (For future use. Currently it is set to 0.)
    Area = 0              #The area that has access to the acquired data.
    Priv = 0              #The access rights required to execute the command.
    HistoryType = 0       #History File Type. Set to 0 for Periodic and Periodic_Event Trends. Set to 4 for Event Trends.
    SamplePeriod = 0      #Sample period of logging (in milliseconds)
    sEngUnits = b"",      #Units of scales. (Set to the units of the trend record.)
    Format = 0            #Format of scales. (Set to the format of the trend record.)
    StartTime = 0,        #The earliest time that a sample can have and be placed in this file, in seconds since 1970.
    EndTime = 0,          #For Periodic Trends the EndTime is always set to the latest possible sample time that can be put into this file. For Event Trends the EndTime is the time of the newest sample stored in the file (one less than the StartTime if there are no samples in the file). Stored as a number of seconds since 1970.
    DataLength = 0        #Shows the number of data items. DataLength = (File Size - HeaderSize) / 2
    FilePointer = 0       #The location of the newest sample in the file, in number of samples from the start of the data portion of the file.(Periodic Trends only).
    EndEvNo = 0           #Event number of the next sample after the last one in this file. (Event Trends only)
    FORMAT = FORMAT6

    def __init__(self,buf):
        self.loadfrombytes(buf)

    def loadfrombytes(self,buf):
        self.Title,self.RawZero,self.RawFull,self.EngZero \
        ,self.EngFull,self.ID,self.FileType,self.Version  \
        ,self.LogName,self.Mode,self.Area,self.Priv,self.HistoryType \
        ,self.SamplePeriod,self.sEngUnits,self.Format \
        ,self.StartTime,self.EndTime,self.DataLength \
        ,self.FilePointer,self.EndEvNo  = unpack(self.FORMAT,buf)
    
    @property
    def pLogName(self):
        return self.LogName[:self.LogName.index(0)].decode()
    @property
    def pStartTime(self):
        return date1601(self.StartTime)
    @property
    def pEndTime(self):
        return date1601(self.EndTime)
    def info(self):
        return f'\n\
ID: {self.ID}\n\
FileType: {self.FileType}\n\
Version: {self.Version}\n\
LogName: {self.pLogName}\n\
Mode: {self.Mode}\n\
Area: {self.Area}\n\
Priv: {self.Priv}\n\
HistoryType: {self.HistoryType}\n\
SamplePeriod: {self.SamplePeriod}\n\
sEngUnits: {self.sEngUnits}\n\
Format: {self.Format}\n\
StartTime: {self.pStartTime}\n\
EndTime:{self.pEndTime}\n\
DataLength: {self.DataLength}\n\
FilePointer: {self.FilePointer}\n\
EndEvNo: {self.EndEvNo}\n\
'

class header6(header):
    """docstring for header6"""
    FORMAT = FORMAT6
    HEADERSIZE = HEADER6SIZE
    DATASIZE = 8
    TYPE = 'd'

class header5(header):
    """docstring for header6"""
    FORMAT = FORMAT5
    HEADERSIZE = HEADER5SIZE
    DATASIZE = 2
    TYPE = 'h'

    @property
    def pStartTime(self):
        return date1900(self.StartTime)
    @property
    def pEndTime(self):
        return date1900(self.EndTime)

class datafile(object):
    header = None

    def __init__(self, filename=''):
        if filename== '': raise Exception("File name required")
        self.filename = filename
        self.readheader()
        
    def readheader(self):
        f = open(self.filename,'rb')
        f.seek(VERSION_FIELD_POS)
        self.Version = ord(f.read(1))
        f.seek(0)
        if self.Version==5:
            self.header = header5(f.read(HEADER5SIZE))
        elif self.Version==6:
            self.header = header6(f.read(HEADER6SIZE))
        f.close()
        filesize = os.path.getsize(self.filename)
        position_max_filesize = (filesize - self.header.HEADERSIZE)//self.header.DATASIZE
        self.position_max = min(position_max_filesize, self.header.FilePointer, self.header.DataLength)

    def readposition(self,position=0,count=1):
        if (self.header==None): raise Exception("Invalid header")
        position_start = min(position, self.position_max)
        count_max = min(count, (self.position_max - position_start))
        f = open(self.filename,'rb')
        f.seek(self.header.HEADERSIZE+position_start*self.header.DATASIZE)
        buf = f.read(count_max*self.header.DATASIZE)
        f.close()
        format_unpack = str(count_max)+self.header.TYPE
        result = unpack(format_unpack,buf)
        return result

    def readpositionstep(self,position=0,count=1,step=0):
        """ read all bytes and unpack. Faster then readpositionstepseek"""
        if (self.header==None): raise Exception("Invalid header")
        position_start = min(position, self.position_max)
        count_max = min(count, (self.position_max - position_start)//(1+step))
        if (step==0):
            format_unpack = str(count_max)+self.header.TYPE
        else:
            format_unpack = (self.header.TYPE+str(self.header.DATASIZE*step)+'x')*(count_max-1)+self.header.TYPE
        f = open(self.filename,'rb')
        f.seek(self.header.HEADERSIZE+position_start*self.header.DATASIZE)
        print(format_unpack)
        buf = f.read(calcsize(format_unpack))
        f.close()
        result = unpack(format_unpack,buf)
        del buf
        return result
 
    def readpositionstepseek(self,position=0,count=1,step=0):
        """ low memory used """
        if (self.header==None): raise Exception("Invalid header")
        f = open(self.filename,'rb')
        position_start = min(position, self.position_max)
        seek = self.header.HEADERSIZE+position_start*self.header.DATASIZE
        count_max = min(count, (self.position_max - position_start)//(1+step))
        result = [0]*count_max
        buf = bytearray()
        for x in range(count_max):
            f.seek(seek)
            buf+=f.read(self.header.DATASIZE)
            # result[x] = unpack(self.header.TYPE, f.read(self.header.DATASIZE))[0]
            seek+=self.header.DATASIZE*(step+1)
            pass
        f.close()
        result = unpack(str(count_max)+self.header.TYPE, buf)
        return result

    def info(self):
        return f'Filename:{self.filename}\nposition_max:{self.position_max}{self.header.info()}'

"""
# example

from citect.data import datafile
d = datafile('00GKC12CP001.009')
print(d.info())


h=loadheader6('00GKC12CP001.000')
print(h)
print(h.Version)
print(bytes(h.LogName))
print(hex(h.Mode))
print(hex(h.Area))
print(hex(h.Priv))
print(hex(h.HistoryType))
print(h.SamplePeriod)
print(h.pStartTime)
print(h.pEndTime)
exit()

"""