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
				"vcount" : "0x0042",
				"button_assign" : "0x0023"}


	def write(self, handle, value):
		self.device.sendline("char-write-req {} {}".format(handle, value))  # write value to requested value handle


	def read(self, handle):
		self.device.sendline("char-read-hnd {}".format(handle))  # read value from requested value handle
		self.device.expect(r"(?<=Characteristic value/descriptor: ).*", timeout=5)  # trim away gatttool excess text
		return self.device.after.splitlines()[0]  # remove next line picked up by pexpect


	def d_calc(self, value):
		return format(int(round( log(value/0.104)/0.075) ), 'x').zfill(2)  # take duration in seconds, convert to hex value for device


	def value_check(self, l, c, d, g):
		if c > 7:  # Count should not exceed 7 (temporary cap, to be removed)
			return False
		if d > 10 or g > 10 or d < 0.11 or g < 0.11:  # Duration on and duration of gap cannot exceed 10 seconds or be below 0.11 seconds (bounds of equation)
			return False

	def vibrate(self, level, count=1, duration_on=0.65, gap=0.65):
		#print "WARNING: Timing for stimulus is only accurate to about .5 seconds; account for this"

		if self.value_check(level, count, duration_on, gap):
			count = str(count)
			level = format(level * 10, 'x').zfill(2)  # conver to hex, ensure 2 digit
			duration_on = self.d_calc(duration_on)
			gap = self.d_calc(gap)
		else:
			raise Exception("Parameter values invalid, see code comments")

		value = "8" + count + "0c" + level + duration_on + gap  # format into packet
		self.write(self.handles["vibrate"], value)


	def beep(self, level, count=1, duration_on=0.65, gap=0.65):
		#print "WARNING: Timing for stimulus is only accurate to about .5 seconds; account for this"

		if self.value_check(level, count, duration_on, gap):
			count = str(count)
			level = format(level * 10, 'x').zfill(2)  # conver to hex, ensure 2 digit
			duration_on = self.d_calc(duration_on)
			gap = self.d_calc(gap)
		else:
			raise Exception("Parameter values invalid, see code comments")

		value = "8" + count + "0c" + level + duration_on + gap  # format into packet
		self.write(self.handles["beep"], value)


	def shock(self, level, count):
		# IMPORTANT NOTE: shock is elicited 0.7 seconds after function called!
		# be sure to account for this time difference in experiments
		svalue = "8" + str(count) + format(level * 10, 'x').zfill(2)
		self.write(self.handles["shock"], svalue)


	def battery(self):
		return int(self.read(self.handles["battery"]), 16)


	def clock(self, sync=False):
		# does not need to be converted to hex, stored as plain decimals
		# value = sec, min, hour, day, ???, month, year
		# the third to last value I'm not sure what it is, im assuming it is assigned day-of-week 0-6 (starting Sunday)
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


	def button_assign(self, assignment, level, count=1, duration_on=0.65, gap=0.65):
		#  Assignments: string, either "vibrate", "beep", or "shock" (shock not working yet)
		a =    {"vibrate" : "01",
			"beep" : "02",
			"shock" : "03"}

		if self.value_check(level, count, duration_on, gap):
			count = str(count)
			level = format(level * 10, 'x').zfill(2)  # conver to hex, ensure 2 digit
			duration_on = self.d_calc(duration_on)
			gap = self.d_calc(gap)
		else:
			raise Exception("Parameter values invalid, see code comments")

		value = "4" + count + "0c" + level + duration_on + gap  # format into packet, first digit = 4 for silent packet

		if assignment == "shock":
			self.write(self.handles[assignment], value.replace("0c", "")[:-4])  # special formatting for shock packet
		else:
			self.write(self.handles[assignment], value)

		self.write(self.handles["button_assign"], a[assignment])

