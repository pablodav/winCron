#!/usr/bin/python

##############################################################################
#  copyright Vincent Lemoine, credits to Emilio Schapira
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
##############################################################################

##############################################################################
#
# 	usage: 	python crontab.py [crontab.txt]
#
#			this program can be used in Windows to schedule task specified
#			in crontab.txt. The program is simular to the linux cron utility
#
##############################################################################

import time
import os
import sys
import string
import signal
import datetime
import tempfile
import ConfigParser

def deltasleep(t=60):    	# due to crontab startup delay, starttime is synced up to t seconds
    sec = float(datetime.datetime.now().strftime("%S.%f")) # get seconds.microseconds
    delta = 0.0          	# init delta
    r = sec % t          	# calculate remainder
    delta = t - r        	# calculate time diff in seconds so 0 <= delta <= t
    return float(delta)  	# return delta as sleep time

def log(msg):				# print msg and log msg logfile
    f = file(logFileName,'a')
    f.write(time.ctime(time.time()) + " " + msg + "\n")
    print(time.ctime(time.time()) + " " + msg)

def signal_handler(signal, frame):	# handle keyboard signals and quit
    print 'You pressed Ctrl+C!'
    sys.exit(0)

def run(command):
    log(command)
    try:
        # For windows prepend "start" to spawn the shell command in another process and avoid waiting
        if os.name == 'nt':
            os.system('start ' + command)
        else:
            os.system(command)
    except:
        log('cron: last command failed to start')

def match(value, expr, interval=1):

	#print "value="+str(value)+"; expr="+str(expr)+"; interval="+str(interval)

	if expr == '*':		# return 1 when expr="*"
		return 1

	values = string.split(expr,'-')	# expr like n-m
	if len(values)>1:			# return 1 for every value in interval n-m
		try:
			if value>=int(values[0]) and value<=int(values[1]):
				return 1
		except:
			pass

	values = string.split(expr,'/')	# expr like */n
	if len(values)>1:				# return 1 for every n occurence
		if int(interval)!=0:
			try:
				if int(value) % int(values[1]) == 0:
					#print "/ 1"
					return 1
			except:
				pass

	values = string.split(expr,',')	# expr like n,m,o,p
	for v in values:
		try:
			if int(v) == value:
				return 1
		except:
			pass

	return 0

def CheckCrontabUpdate(crontabFileName):

	# whenever crontabFileName has been changed a new internal $crontab.bin is generated
	#	- replace symbolic names (@daily, @mon, etc)
	#	- remove comment and empty lines

	# read config.ini
	configfile = 'crontab.ini'
	config = ConfigParser.RawConfigParser()
	config.read(configfile)

	try:
		# Read config variables
		filetime    = config.getint('crontab','filetime')

	except:
		print datetime.datetime.now(), 'error reading config file, config = ',configfile
		sys.exit(4)

	try:
		# os.stat(filenme) get file attributes
		(mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(crontabFileName)
	except:
		print datetime.datetime.now(), 'error reading config file, crontab = ',crobtabFileName
		sys.exit(4)

	if filetime!=mtime:		#	check if modified time has been changed
		#print filetime, mtime

		try:
			lines = file(crontabFileName,'r').readlines()	# Read the crontab file

			# replace special keywords by standard syntax before processing
			lines = [keywords.replace('@year','0 0 1 1 *') for keywords in lines]
			lines = [keywords.replace('@daily','0 0 * * *') for keywords in lines]
			lines = [keywords.replace('@midnight','0 0 * * *') for keywords in lines]
			lines = [keywords.replace('@noon','0 12 * * *') for keywords in lines]
			lines = [keywords.replace('@hourly','0 * * * *') for keywords in lines]
			lines = [keywords.replace('@reboot','#reboot') for keywords in lines]

			lines = [keywords.replace('@monthly','0 0 1 * *') for keywords in lines]
			lines = [keywords.replace('@weekly','0 0 * * 0') for keywords in lines]

			lines = [keywords.replace('@mon','0 0 * * 0') for keywords in lines]
			lines = [keywords.replace('@tue','0 0 * * 1') for keywords in lines]
			lines = [keywords.replace('@wed','0 0 * * 2') for keywords in lines]
			lines = [keywords.replace('@thu','0 0 * * 3') for keywords in lines]
			lines = [keywords.replace('@fri','0 0 * * 4') for keywords in lines]
			lines = [keywords.replace('@sat','0 0 * * 5') for keywords in lines]
			lines = [keywords.replace('@sun','0 0 * * 6') for keywords in lines]

			log("cron: generating internal crobtab: %s" % crontabGenerated)
			cron = open(crontabGenerated, 'w')
			for line in lines:
				if line[0] != '#' and len(string.strip(line)) != 0:
					cron.write(line)
			cron.close()

		except:	# issue error message when crontab cannot be opened
			log('cron: error opening %s file' % crontabFileName)

		config.set('crontab','filetime', mtime)	# set new m(odified)time
		with open('crontab.ini', 'wb') as configfile:
			config.write(configfile)

signal.signal(signal.SIGINT, signal_handler)	# setup signal handler

tmpdir = tempfile.gettempdir() # get the current temporary directory

if os.name == 'nt':
	tmpdir=tmpdir+"\\"
else:
	tmpdir=tmpdir+"/"

# default file names, pid and log file to temp dir
crontabFileName	= "crontab.txt"
logFileName 	= tmpdir+"crontab.log"
pidFileName 	= tmpdir+"crontab.pid"
crontabGenerated= "$crontab.bin"

try:	# override defaults with arguments
	crontabFileName	= sys.argv[1]
except:
	pass

# Write the pid in the current directory.
f = file(pidFileName,'w')
f.write(str(os.getpid()))
f.close()

# Log cron start
log('cron: started with file %s' % crontabFileName)
log('cron: wait %s seconds for first crontab scan' % deltasleep(60))

# wait to next minute (hh:mm:00)
time.sleep(deltasleep(60))

while 1:	# loop forever

	#log('cron: scanning for tasks to be executed')
	time.sleep(1)				# to be sure we passed the minute (hh:mm:01)

	# generated new internal $crontab.bin if crontab.txt has been changed
	CheckCrontabUpdate(crontabFileName)

	curTime = time.localtime()	# get current localtime

	# 	format curTime : time.struct_time(tm_year=2016, tm_mon=11, tm_mday=10, tm_hour=12, tm_min=11, tm_sec=4, tm_wday=3, tm_yday=315, tm_isdst=0)
	#
	#	0	=	year	(tm_year)	year
	#	1	=	month	(tm_mon)	(1,...,12)
	#	2	=	day		(tm_mday)	(0,...,28[,29[,30[,31]]])
	#	3	=	hour	(tm_hour)	(0,...,23)
	#	4	=	minute	(tm_min)	(0,...,59)
	#	5	=	second	(tm_sec)	(0,...,59)
	#	6	=	weekday	(tm_wday)	(0,...,6)	(0=Mon,...,6=Sun)
	#	7	=	ytd		(tm_yday)	day of year (1,...,365[,366])
	#	8	=	dst		(tm_isdst)	daylight saving time [0|1]
	#

	try:
		lines = file(crontabGenerated,'r').readlines()	# Read the generated $crontab.bin file
		lineNum = 1										# line numbering

		for line in lines:								# process every line in lines
			if line[0] != '#' and len(string.strip(line)) != 0:	# Ignore comments and empty lines
				try:
					tokens = string.split(line)
					# print tokens,str(tokens[0])
					# See if the cron entry matches the current time minute
					timeMatch = match(curTime[4],str(tokens[0]))
					# See if the cron entry matches the current time hour
					timeMatch = timeMatch and match(curTime[3],tokens[1])
					# See if the cron entry matches the current day
					timeMatch = timeMatch and match(curTime[2],tokens[2])
					# See if the cron entry matches the current month
					timeMatch = timeMatch and match(curTime[1],tokens[3])
					# See if the cron entry matches the current weekday (in crontab 0=Monday,...,6=Sunday)
					timeMatch = timeMatch and match(curTime[6],tokens[4],0)

					if timeMatch:	# if true fire command
						run(string.join(tokens[5:]))

				except:	# issue error message when crontab contains errors
					log('cron: error parsing line %i of %s' % (lineNum, crontabGenerated))

			lineNum = lineNum + 1

	except:	# issue an error message when crontab cannot be opened
		log('cron: error opening %s file' % crontabFGenerated)

	time.sleep(deltasleep(60)) # wait 60 seconds, until next minute

