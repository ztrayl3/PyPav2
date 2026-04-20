from bleak import BleakClient
from threading import Thread
import asyncio
from math import log
from datetime import datetime

class Pavlok():

	def __init__(self, mac="F8:77:23:11:F7:46"):  # mac address defaults to my testing unit if not specified
		self.e_loop = asyncio.get_event_loop()

		def bleak_thread(loop):
			asyncio.set_event_loop(loop)
			loop.run_forever()
		Thread(target=bleak_thread, args=(self.e_loop,)).start()

		self.client = BleakClient(mac)

		asyncio.run_coroutine_threadsafe(self.client.connect(), self.e_loop).result(10)

		# gatttool sends commands by handle, below are all the handles the program has control over so far (more to come!)
		self.handles = {"vibrate" : 15,
				"beep" : 18,
				"shock" : 21,
				"battery" : 106,
				"clock" : 28,
				"button_assign" : 34}


	def write(self, handle, value):  # wrapper for gatttool/pexpect write
		asyncio.run_coroutine_threadsafe(self.client.write_gatt_char(handle, bytes.fromhex(value), response=True), self.e_loop)

	def read(self, handle):  # wrapper for gatttool/pexpect read
		return asyncio.run_coroutine_threadsafe(self.client.read_gatt_char(handle), self.e_loop).result(5)

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
		self.write(self.handles["vibrate"], value)

	def beep(self, level, count=1, duration_on=0.65, gap=0.65):  # send beep command to Pavlok 2

		if self.value_check(level, count, duration_on, gap):  # proceed as long as parameters are okay
			count = str(count)
			level = format(level * 10, 'x').zfill(2)  # conver to hex, ensure 2 digit format
			duration_on = self.d_calc(duration_on)
			gap = self.d_calc(gap)
		else:
			raise Exception("Parameter values invalid")

		value = "8" + count + "0c" + level + duration_on + gap  # format into packet to be sent to Pavlok 2
		self.write(self.handles["beep"], value)

	def shock(self, level, count=1):  # send shock command to Pavlok 2, should be noted that my measurements show the shock elicited 0.7 seconds after function call
		# shock lacks duration on and gap parameters as a hardware feature, repeated shock timing should be handled outside of this function

		if self.value_check(level, count):  # proceed as long as parameters are okay
			svalue = "8" + str(count) + format(level * 10, 'x').zfill(2)  # format into packet to be sent to Pavlok 2, ensuring hex, 2 digit format
		else:
			raise Exception("Parameter values invalid")
		self.write(self.handles["shock"], svalue)

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
			self.write(self.handles[assignment], value.replace("0c", "")[:-4])  # special formatting for shock packet, shorter than other stimulus
		else:
			self.write(self.handles[assignment], value)

		self.write(self.handles["button_assign"], a[assignment])

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
			self.write(self.handles["clock"], time)
			return self.read(self.handles["clock"])
		else:
			return self.read(self.handles["clock"])  # if we aren't syncing, just return clock time

	def battery(self):  # check battery level, returns human readable integer percentage
		return int(self.read(self.handles["battery"]), 16)

	def vibe_count(self):  # check vibration tally, returns human readable integer
		raise NotImplementedError

	def beep_count(self):  # check beep tally, returns human readable integer
		raise NotImplementedError

	def shock_count(self):  # check shock tally, returns human readable integer
		raise NotImplementedError
