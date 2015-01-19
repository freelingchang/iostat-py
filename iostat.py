#!/usr/bin/env python
#coding: utf-8
#file   : iostat.py 
#author : freelingchang
#修改使支持2.6


import os
import re
import sys
import time
import commands
from datetime import datetime
import copy
import thread
import logging
from pprint import pprint
import pickle

DISK='sda'
logFile = '/dev/shm/iostst.log'
stateFile = '/sys/block/'+DISK+'/stat'
logPath=os.path.split(os.path.realpath(__file__))[0]
def getStateContent(statFile):
    f = open(stateFile,'r')
    stateContent = f.read()
    f.close
    return stateContent
def tonum(n):
    if type(n) == type(''):
        if n.isdigit():
            return int(n)
        return n
def writeState(stateDict):
    f = open(logFile,'w')
    pickle.dump(stateDict,f)
    f.close()
def readLastState(stateDict):
    global logFile
    if not os.path.exists('/dev/shm'):
        logFile = logPath+'/iostat.log'
    if not  os.path.isfile(logFile):
        writeState(stateDict)
        return stateDict
    st = os.stat(logFile)
    mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = st
    if size == 0:
        writeState(stateDict)
        return stateDict
    f = open(logFile,'r')
    #print(f.read());
    lastStateDict = pickle.load(f)
    f.close()
    writeState(stateDict)
    return lastStateDict

def setStateDict(line):
    d = {}
    r_ios, r_merges, r_sec, r_ticks, w_ios, w_merges, w_sec, w_ticks, ios_pgr, tot_ticks, rq_ticks = line.split()
    del line
    for k  in locals().items():
    #    print k[1]
        d[k[0]] = tonum(k[1])
    #d = {k: tonum(v) for k, v in locals().items() }
    d['ts'] = time.time()
    return d
#:rrqm/s   : The number of read requests merged per second that were queued to the device.    #( rd_merges[1] - rd_merges[0] )
#:wrqm/s   :
#:r/s      : The number of read requests that were issued to the device per second.           #(rd_ios[1] - rd_ios[0]) #:w/s      : #:rkB/s    : The number of kilobytes read from the device per second.                         #( rd_sectors[1] - rd_sectors[0] ) * sector_size
#:wkB/s    :

#:avgrq-sz : (平均请求大小)The average size **in sectors** of the requests that were issued to the device.
            #( ( rd_sectors[1] - rd_sectors[0] ) + ( wr_sectors[1] - wr_sectors[0] ) ) / (rd_ios[1] - rd_ios[0]) + (wr_ios[1] - wr_ios[0])
#:avgqu-sz : The average queue length of the requests that were issued to the device.
            #这不是ios_pgr, 而是: (rq_ticks[1] - rq_ticks[0]) / 1000 这是什么原理.

#:await    : (等待时间)The average time (in milliseconds) for I/O requests issued to the  device  to  be  served
            #( ( rd_ticks[1] - rd_ticks[0] ) + ( wr_ticks[1] - wr_ticks[0] ) ) / (rd_ios[1] - rd_ios[0]) + (wr_ios[1] - wr_ios[0])
#:svctm    : (服务时间)The average service time (in milliseconds) for I/O requests that were issued to the device.  (和上一个很像)
            #util/(rd_ios[1] - rd_ios[0]) + (wr_ios[1] - wr_ios[0])
#:util     : Percentage  of  CPU time during which I/O requests were issued to the device
            #(tot_ticks[1] - tot_ticks[0]) / 1000 * 100

def calc(last, curr):
    SECTOR_SIZE = 512
    stat = {}

    def diff(field):
        return (curr[field] - last[field]) / (curr["ts"] - last["ts"])

    stat['rrqm/s']   = diff('r_merges')
    stat['wrqm/s']   = diff('w_merges')
    stat['r/s']      = diff('r_ios')
    stat['w/s']      = diff('w_ios')
    stat['rkB/s']    = diff('r_sec') * SECTOR_SIZE / 1024
    stat['wkB/s']    = diff('w_sec') * SECTOR_SIZE / 1024

    stat['avqqu-sz'] = diff('rq_ticks') / 1000
    #print 'tot_ticks', curr['tot_ticks'], last['tot_ticks']
    stat['util']     = diff('tot_ticks')/10 #???

    if diff('r_ios') + diff('w_ios') > 0:
        stat['avgrq-sz'] = ( diff('r_sec') + diff('w_sec') ) / ( diff('r_ios') + diff('w_ios') )
        stat['await']    = ( diff('r_ticks') + diff('w_ticks') ) / ( diff('r_ios') + diff('w_ios') )
        stat['svctm']    = diff('tot_ticks') / ( diff('r_ios') + diff('w_ios') )
    else:
        stat['avgrq-sz'] = 0
        stat['await']    = 0
        stat['svctm']    = 0

    return stat


def printstat(stat):
    print datetime.now(),
    for k, v in stat.items():
        print '%s: %.2f' % (k, float(v)) ,
    print ''

def check():
    stateContent = getStateContent(stateFile)
    nowStateDict = setStateDict(stateContent)
    lastStateDict = readLastState(nowStateDict)
    stat = calc(lastStateDict,nowStateDict)
    printstat(stat)

if __name__ == "__main__":
    check()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4


