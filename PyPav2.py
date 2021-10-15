import pexpect
from math import log
from datetime import datetime

class Pavlok():

	def __init__(self, mac="FA:E5:08:A8:DB:D7"):  # mac address defaults to my testing unit if not specified
		self.device = pexpect.spawn("gatttool -t random -b {} -I".format(mac))  # core of the function, based around gatttool (a component of Bluez)

		self.device.sendline("connect")
		self.device.expect("Connection successful", timeout=5)  # establish a connection with the Pavlok 2

		# gatttool sends commands by uuid, below are all the uuids the program has control over so far (more to come!)
		self.uuids = {"vibrate" : "00001001-0000-1000-8000-00805f9b34fb",
				"beep" : "00001002-0000-1000-8000-00805f9b34fb",
				"shock" : "00001003-0000-1000-8000-00805f9b34fb",
				"battery" : "00002a19-0000-1000-8000-00805f9b34fb",
				"clock" : "00001005-0000-1000-8000-00805f9b34fb",
				"scount" : "00002005-0000-1000-8000-00805f9b34fb",
				"bcount" : "00002006-0000-1000-8000-00805f9b34fb",
				"vcount" : "00002007-0000-1000-8000-00805f9b34fb",
				"button_assign" : "00001007-0000-1000-8000-00805f9b34fb"}
		# switch to pygatt and use uuids

	def write(self, uuid, value):  # wrapper for gatttool/pexpect write
		self.device.sendline("char-write-req {} {}".format(uuid, value))  # write value to requested value uuid


	def read(self, uuid):  # wrapper for gatttool/pexpect read
		self.device.sendline("char-read-hnd {}".format(uuid))  # read value from requested value uuid
		self.device.expect(r"(?<=Characteristic value/descriptor: ).*", timeout=5)  # trim away gatttool excess text
		return self.device.after.splitlines()[0]  # remove next line picked up by pexpect, unnecessary


	def d_calc(self, value):  # mathmatical function to calculate duration in hex when given desired number of seconds (see readme for more explanation)
		return format(int(round( log(value/0.104)/0.075) ), 'x').zfill(2)  # take duration in seconds, convert to hex value for device


	def value_check(self, l, c, d=0.65, g=0.65):  # check parameters before sending information to Pavlok 2 (these limits imposed as Pavlok performs unexpectedly outside of them)
		if l < 0 or l > 10:  # Level should not exceed 10 or be negative
			return False
		elif c > 7:  # Count should not exceed 7 (temporary cap, to be removed)
			return False
		elif d > 10 or g > 10 or d < 0.11 or g < 0.11:  # Duration on and duration of gap cannot exceed 10 seconds or be below 0.11 seconds (bounds of equation)
			return False
		else:
			return True


	def vibrate(self, level, count=1, duration_on=0.65, gap=0.65):  # send vibrate command to Pavlok 2

		if self.value_check(level, count, duration_on, gap):  # proceed as long as parameters are okay
			count = str(count)
			level = format(level * 10, 'x').zfill(2)  # conver to hex, ensure 2 digit format
			duration_on = self.d_calc(duration_on)
			gap = self.d_calc(gap)
		else:
			raise Exception("Parameter values invalid")

		value = "8" + count + "0c" + level + duration_on + gap  # format into packet to be sent to Pavlok 2
		self.write(self.uuids["vibrate"], value)


	def beep(self, level, count=1, duration_on=0.65, gap=0.65):  # send beep command to Pavlok 2

		if self.value_check(level, count, duration_on, gap):  # proceed as long as parameters are okay
			count = str(count)
			level = format(level * 10, 'x').zfill(2)  # conver to hex, ensure 2 digit format
			duration_on = self.d_calc(duration_on)
			gap = self.d_calc(gap)
		else:
			raise Exception("Parameter values invalid")

		value = "8" + count + "0c" + level + duration_on + gap  # format into packet to be sent to Pavlok 2
		self.write(self.uuids["beep"], value)


	def shock(self, level, count=1):  # send shock command to Pavlok 2, should be noted that my measurements show the shock elicited 0.7 seconds after function call
		# shock lacks duration on and gap parameters as a hardware feature, repeated shock timing should be handled outside of this function

		if self.value_check(level, count):  # proceed as long as parameters are okay
			svalue = "8" + str(count) + format(level * 10, 'x').zfill(2)  # format into packet to be sent to Pavlok 2, ensuring hex, 2 digit format
		else:
			raise Exception("Parameter values invalid")
		self.write(self.uuids["shock"], svalue)


	def button_assign(self, assignment, level, count=1, duration_on=0.65, gap=0.65):  # Assign a stimulus to the Pavlok 2's main button
		#  Assignments: string, either "vibrate", "beep", or "shock" (shock not working yet)
		a =    {"vibrate" : "01",
			"beep" : "02"}

		if self.value_check(level, count, duration_on, gap):  # proceed as long as parameters are okay
			count = str(count)
			level = format(level * 10, 'x').zfill(2)  # conver to hex, ensure 2 digit format
			duration_on = self.d_calc(duration_on)
			gap = self.d_calc(gap)
		else:
			raise Exception("Parameter values invalid, see code comments")

		value = "4" + count + "0c" + level + duration_on + gap  # format into packet, first digit = 4 for silent packet (does not elicit stimulus, just assigns it)

		if assignment == "shock":
			self.write(self.uuids[assignment], value.replace("0c", "")[:-4])  # special formatting for shock packet, shorter than other stimulus
		else:
			self.write(self.uuids[assignment], value)

		self.write(self.uuids["button_assign"], a[assignment])


	def clock(self, sync=False, utcd=0, dst=False):  # access Pavlok 2 clock, with utcd as difference from UTC in hours (int) and dst as Daylight Savings Time (bool)
		# does not need to be converted to hex, stored as plain decimals
		# value = sec, min, hour, day, week, month, year
		# the third to last value I'm not sure what it is, im assuming it is assigned day-of-week 0-6 (starting Sunday)
		if sync:  # synchronize system clock and device clock, using difference from UTC and daylight savings time if needed
			a = datetime.now().strftime('%S %M %H %d 0%w %m %y').split(" ")  # match Pavlok 2 time string formatting
			if dst:  # perform DST subtraction if needed, and also UTC difference
				a[2] = str(int(a[2]) + utcd - 1)
			else:
				a[2] = str(int(a[2]) + utcd)
			time = ''.join(a)
			self.write(self.uuids["clock"], time)
			return self.read(self.uuids["clock"])
		else:
			return self.read(self.uuids["clock"])  # if we aren't syncing, just return clock time


	def battery(self):  # check battery level, returns human readable integer percentage
		return int(self.read(self.uuids["battery"]), 16)


	def vibe_count(self):  # check vibration tally, returns human readable integer
		return int(self.read(self.uuids["vcount"]), 16)


	def beep_count(self):  # check beep tally, returns human readable integer
		return int(self.read(self.uuids["bcount"]), 16)


	def shock_count(self):  # check shock tally, returns human readable integer
		return int(self.read(self.uuids["scount"]), 16)
