#!/usr/bin/python
#coding:utf-8
#Date  2014.11.6
#Author:freelingchang@gmail.com
import os,sys,time
try:
    from multiprocessing import cpu_count
    cpu_num=cpu_count()
except ImportError:
    cpu_num=int(os.popen("cat /proc/cpuinfo |grep process |wc -l").read().rstrip())
#想到一个新思路，完全没有必要设置间隔时间，只要将时间戳写入tmp文件对时间戳即可
#因为cpu时间统计单位为10ms，所以要多除以100
#为了避免IO影响，tmp.db 应该写入tmpfs
cache_file='/dev/shm/cpu_count.db'
cache_path=os.path.split(os.path.realpath(__file__))[0]
#cache_file=cache_path+'/cpu_count.db'
f = open('/proc/stat','r')
status_now=f.readline().strip()
status_now=status_now+' '+("%.3f" % time.time())
status_now_list = status_now.split()
cpu_idle_now=float(status_now_list[4])
cpu_iowait_now=float(status_now_list[5])
f.close()
if not os.path.exists('/dev/shm'):
    cache_file=cache_path+'/cpu_count.db'
if not  os.path.isfile(cache_file):
    try:
        f = open(cache_file,'w')
        f.write(status_now)
        f.close()
        sys.exit(0)
    except Exception,ex:
        cache_file=cache_path+'/cpu_count.db'
        f = open(cache_file,'w')
        f.write(status_now)
        f.close()
        sys.exit(0)
f = open(cache_file,'r')
status_last=f.read()
f.close()
f = open(cache_file,'w')
f.write(status_now)
f.close()
if not status_last:
    f = open(cache_file,'w')
    f.write(status_now)
    f.close()
    sys.exit(0)
status_last_list = status_last.split()
now_time=time.time()
last_time=status_last_list[-1]
time=now_time-float(last_time)
if time == 0:
    sys.exit(0)
#print '已过去 %.3f 秒' % time
cpu_idle_last=float(status_last_list[4])
cpu_iowait_last=float(status_last_list[5])
#因为/proc/stat 单位时cpu时间分片，一般为10ms,除以统计间隔时间
#iowait=(cpu_iowait_now-cpu_iowait_last)
cpu_iowait=(cpu_iowait_now-cpu_iowait_last)/(time*cpu_num)
cpu_idle=(cpu_idle_now-cpu_idle_last)/(time*cpu_num)
cpu_usage=100-cpu_idle-cpu_iowait
def status():
    print("idle %.2f%%") % cpu_idle,
    print("use %.2f%%") % cpu_usage,
    print("iowait %.2f%%") % cpu_iowait
if cpu_usage > 95:
    status()
    sys.exit(2)
elif cpu_iowait > 20:
    status()
    sys.exit(2)
else:
    status()
    sys.exit(0)
