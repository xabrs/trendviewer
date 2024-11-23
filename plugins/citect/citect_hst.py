from .citect_data import date1601,date1900, datafile
import logging
from struct import unpack, calcsize
from datetime import timedelta
import os

log = logging.getLogger('citect')

HSTVERSIONPOS = 0x8A

ROWFORMAT = "<272s8shh20x64s8x2xliiil8siQQiiq6x"
ROWSIZE = calcsize(ROWFORMAT) #448

ROW5FORMAT = "<144s8shh4x64s8x2xliiil8silliil2x"
ROW5SIZE = calcsize(ROW5FORMAT) #288

class Row(object):
    FORMAT = ROWFORMAT
    FileName = b"",
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
    
    def __init__(self,buf):
        self.loadfrombytes(buf)

    def loadfrombytes(self,buf):
        self.FileName \
        ,self.ID,self.FileType,self.Version  \
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
    @property
    def pFileName(self):
        return self.FileName[:self.FileName.index(0)].decode()
    
    def info(self):
        return f"\nFileName:{self.pFileName}\nLogName: {self.pLogName}\nStartTime: {self.pStartTime}\nEndTime:{self.pEndTime}\nDataLength: {self.DataLength}\nFilePointer: {self.FilePointer}\n"

class Row5(Row):
    FORMAT = ROW5FORMAT
    FileName = b"",
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
    
    @property
    def pStartTime(self):
        return date1900(self.StartTime)
    @property
    def pEndTime(self):
        return date1900(self.EndTime)

class HST(object):
    """docstring for HST"""
    rows = []
    def __init__(self,tag, directory=""):
        self.directory=directory
        self.filename = os.path.join(directory,tag+".HST")
        f = open(self.filename,"rb")
        _ROW = Row
        _ROWSIZE = ROWSIZE
        f.seek(HSTVERSIONPOS)
        if ord(f.read(1))==5:
            _ROW = Row5
            _ROWSIZE = ROW5SIZE
            log.debug("HST version 5")

        self.filesize = os.path.getsize(self.filename)
        pos = 0xB0
        while pos<self.filesize:
            f.seek(pos)
            r = _ROW(f.read(_ROWSIZE))
            self.rows.append(r)
            pos +=_ROWSIZE
        f.close()

    def get_index_by_date(self, dt):
        for x in reversed(range(len(self.rows))):
            if (dt <= self.rows[x].pEndTime) and (dt >= self.rows[x].pStartTime):
                return x

    def get_row_by_date(self, dt):
        x = self.get_index_by_date(dt)
        if x is not None: return self.rows[x]
    
    def get_rows_by_daterange(self, tstart, tend):
        x0 = self.get_index_by_date(tstart)
        x1 = self.get_index_by_date(tend)
        if x1<x0: x0, x1 = x1, x0
        return reversed(range(x0, x1+1))

    def get_values_by_daterange(self, tstart, tend):
        row_nums = self.get_rows_by_daterange(tstart, tend)
        if tstart > tend: tstart, tend  = tend, tstart
        deltatime = tend - tstart
        deltatime = deltatime.days*86400 + deltatime.seconds
        if deltatime < 7200: # 2 hours - 1 second step
            timestep = 1
        elif deltatime < 172800: # 2 days - 1 minute
            timestep = 60
        elif deltatime < 604800: # 7 days - 5 minute
            timestep = 300
        elif deltatime < 124416000:  # 60 days - 1 hour
            timestep = 3600
        else: # 3 hour
            timestep = 10800
        log.debug(f'delta time={deltatime}, timestep = {timestep}')
        lasttend = 0
        result = []
        t = tstart

        for i in row_nums:
            if self.directory == "":
                filename=self.rows[i].pFileName
            else:
                filename = os.path.join(self.directory,os.path.basename(self.rows[i].pFileName))
            data = datafile(filename)
            log.debug(data.info())
            buf = []
            position = int((tstart.timestamp() - data.header.pStartTime.timestamp())/(data.header.SamplePeriod/1000))
            position = max(0,position)
            _tstart = max(lasttend, tstart.timestamp(),data.header.pStartTime.timestamp())
            _tend = min(tend.timestamp(),data.header.pEndTime.timestamp())
            count = int(_tend - _tstart) // timestep
            step = timestep - 1
            log.debug('tstart={}, tend={}, timestep={}, '
                      'position={}, count={}, step={}'.format(_tstart,_tend,timestep,position,count,step))
            buf = data.readpositionstep(position, count, step)
            lasttend = data.header.pEndTime.timestamp()
            for x in buf:
                result.append({"dt":t,"v":x})
                t += timedelta(seconds=timestep)
        return result