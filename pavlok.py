import pexpect
from math import log
from datetime import datetime

class Pavlok():

	def __init__(self, mac="FA:E5:08:A8:DB:D7"):  # mac address defaults to my testing unit if not specified
		self.device = pexpect.spawn("gatttool -t random -b {} -I".format(mac))

		self.device.sendline("connect")
		self.device.expect("Connection successful", timeout=5)

		self.handles = {"vibrate" : "0x0010",
				"beep" : "0x0013",
				"shock" : "0x0016",
				"battery" : "0x006d",
				"clock" : "0x001d",
				"scount" : "0x003a",
				"bcount" : "0x003e",
				"vcount" : "0x0042"}


	def write(self, handle, value):
		self.device.sendline("char-write-req {} {}".format(handle, value))  # write value to requested value handle


	def read(self, handle):
		self.device.sendline("char-read-hnd {}".format(handle))  # read value from requested value handle
		self.device.expect(r"(?<=Characteristic value/descriptor: ).*", timeout=5)  # trim away gatttool excess text
		return self.device.after.splitlines()[0]  # remove next line picked up by pexpect


	def d_calc(self, value):
		return format(int(round( log(value/0.104)/0.075) ), 'x').zfill(2)  # take duration in seconds, convert to hex value for device


	def vibrate(self, level, count=1, duration_on=0.65, gap=0.65):
		#print "WARNING: Timing for stimulus is only accurate to about .5 seconds; account for this"

		if count < 8:
			count = str(count)
		else:
			raise Exception("count should not exceed 7")
		level = format(level * 10, 'x').zfill(2)  # conver to hex, ensure 2 digit
		if duration_on > 10 or gap > 10 or duration_on < 0.11 or 0 < gap < 0.11:
			raise Exception("duration on and duration of gap cannot exceed 10 seconds or be below 0.11 seconds")
		else:
			duration_on = self.d_calc(duration_on)
			gap = self.d_calc(gap)

		value = "8" + count + "0c" + level + duration_on + gap  # format into packet
		self.write(self.handles["vibrate"], value)


	def beep(self, level, count=1, duration_on=0.65, gap=0.65):
		#print "WARNING: Timing for stimulus is only accurate to about .5 seconds; account for this"

		if count < 8:
			count = str(count)
		else:
			raise Exception("count should not exceed 7")
		level = format(level * 10, 'x').zfill(2)  # conver to hex, ensure 2 digit
		if duration_on > 10 or gap > 10 or duration_on < 0.11 or gap < 0.11:
			raise Exception("duration on and duration of gap cannot exceed 10 seconds or be below 0.11 seconds")
		else:
			duration_on = self.d_calc(duration_on)
			gap = self.d_calc(gap)

		value = "8" + count + "0c" + level + duration_on + gap  # format into packet
		self.write(self.handles["beep"], value)


	def shock(self, value, count):
		# IMPORTANT NOTE: shock is elicited 0.7 seconds after function called!
		# be sure to account for this time difference in experiments
		svalue = "8" + str(count) + format(value * 10, 'x').zfill(2)
		self.write(self.handles["shock"], svalue)


	def battery(self):
		return int(self.read(self.handles["battery"]), 16)


	def clock(self, sync=False):
		# does not need to be converted to hex, stored as plain decimals
		# value = sec, min, hour, day,  ???, month, year
		# the third to last value I have no idea what it could be so it is assigned day-of-week 0-6 (s$
        if sync:  # synchronize system clock and device clock 
        	time = datetime.now().strftime('%S%M%H%d0%w%m%y')
            self.write(self.handles["clock"], time)
			return self.read(self.handles["clock"])
		else:
			return self.read(self.handles["clock"])


	def shock_count(self):
		return int(self.read(self.handles["scount"]), 16)


	def beep_count(self):
		return int(self.read(self.handles["bcount"]), 16)


	def vibe_count(self):
		return int(self.read(self.handles["vcount"]), 16)

