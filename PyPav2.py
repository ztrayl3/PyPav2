import asyncio
from math import log
from datetime import datetime

from bleak import BleakClient

class Pavlok:
	# Map logical name -> characteristic UUID. Original PyPa used ATT value handles from
	# gatttool; bleak resolves characteristics by UUID (or char object) so we use UUIDs,
	# which are also stable across firmware revisions where handle numbering can shift.
	HANDLES = {
		"vibrate":       "00001001-0000-1000-8000-00805f9b34fb",
		"beep":          "00001002-0000-1000-8000-00805f9b34fb",
		"shock":         "00001003-0000-1000-8000-00805f9b34fb",
		"clock":         "00001005-0000-1000-8000-00805f9b34fb",
		"button_assign": "00001007-0000-1000-8000-00805f9b34fb",
		"scount":        "00002005-0000-1000-8000-00805f9b34fb",
		"bcount":        "00002006-0000-1000-8000-00805f9b34fb",
		"vcount":        "00002007-0000-1000-8000-00805f9b34fb",
		"battery":       "00002a19-0000-1000-8000-00805f9b34fb",
	}

	def __init__(self, mac="<PAVLOK MAC ADDRESS>"):
		self.mac = mac
		self.client = BleakClient(mac)

	# ----- connection management -----
	async def __aenter__(self):
		await self.client.connect()
		return self

	async def __aexit__(self, exc_type, exc, tb):
		try:
			await self.client.disconnect()
		except EOFError:
			# bleak/dbus_fast can raise EOFError on disconnect with some BlueZ versions; benign
			pass

	async def connect(self):
		await self.client.connect()

	async def disconnect(self):
		try:
			await self.client.disconnect()
		except EOFError:
			pass

	# ----- low-level I/O -----
	async def write(self, handle, value):  # value: hex string, as in original
		await self.client.write_gatt_char(handle, bytes.fromhex(value), response=True)

	async def read(self, handle):  # returns hex string to mirror original behavior
		data = await self.client.read_gatt_char(handle)
		return data.hex()

	# ----- helpers -----
	def d_calc(self, value):  # seconds -> 2-digit hex duration byte (see readme)
		return format(int(round(log(value / 0.104) / 0.075)), "x").zfill(2)

	def value_check(self, l, c, d=0.65, g=0.65):  # parameter bounds enforced by device behavior
		if l < 0 or l > 10:
			return False
		elif c > 7:
			return False
		elif d > 10 or g > 10 or d < 0.11 or g < 0.11:
			return False
		else:
			return True

	# ----- stimulus commands -----
	async def vibrate(self, level, count=1, duration_on=0.65, gap=0.65):
		if not self.value_check(level, count, duration_on, gap):
			raise ValueError("Parameter values invalid")
		count = str(count)
		level = format(level * 10, "x").zfill(2)
		duration_on = self.d_calc(duration_on)
		gap = self.d_calc(gap)

		value = "8" + count + "0c" + level + duration_on + gap
		await self.write(self.HANDLES["vibrate"], value)

	async def beep(self, level, count=1, duration_on=0.65, gap=0.65):
		if not self.value_check(level, count, duration_on, gap):
			raise ValueError("Parameter values invalid")
		count = str(count)
		level = format(level * 10, "x").zfill(2)
		duration_on = self.d_calc(duration_on)
		gap = self.d_calc(gap)

		value = "8" + count + "0c" + level + duration_on + gap
		await self.write(self.HANDLES["beep"], value)

	async def shock(self, level, count=1):
		# shock has no duration_on/gap; ~0.7s latency between repeated shocks (hardware)
		if not self.value_check(level, count):
			raise ValueError("Parameter values invalid")
		svalue = "8" + str(count) + format(level * 10, "x").zfill(2)
		await self.write(self.HANDLES["shock"], svalue)

	async def button_assign(self, assignment, level, count=1, duration_on=0.65, gap=0.65):
		# assignment: "vibrate", "beep", or "shock"
		a = {"vibrate": "01", "beep": "02"}

		if not self.value_check(level, count, duration_on, gap):
			raise ValueError("Parameter values invalid, see code comments")
		count = str(count)
		level = format(level * 10, "x").zfill(2)
		duration_on = self.d_calc(duration_on)
		gap = self.d_calc(gap)

		# leading "4" = silent packet (assigns stimulus without firing it)
		value = "4" + count + "0c" + level + duration_on + gap

		if assignment == "shock":
			await self.write(self.HANDLES[assignment], value.replace("0c", "")[:-4])
		else:
			await self.write(self.HANDLES[assignment], value)

		await self.write(self.HANDLES["button_assign"], a[assignment])

	# ----- clock -----
	async def clock(self, sync=False, utcd=0, dst=False):
		# value layout: sec, min, hour, day, dow(0-6, Sun=0), month, year — stored as decimal, not hex
		if sync:
			a = datetime.now().strftime("%S %M %H %d 0%w %m %y").split(" ")
			if dst:
				a[2] = str(int(a[2]) + utcd - 1)
			else:
				a[2] = str(int(a[2]) + utcd)
			time = "".join(a)
			await self.write(self.HANDLES["clock"], time)
		return await self.read(self.HANDLES["clock"])

	# ----- counters / battery -----
	async def battery(self):
		return int(await self.read(self.HANDLES["battery"]), 16)

	async def vibe_count(self):
		return int(await self.read(self.HANDLES["vcount"]), 16)

	async def beep_count(self):
		return int(await self.read(self.HANDLES["bcount"]), 16)

	async def shock_count(self):
		return int(await self.read(self.HANDLES["scount"]), 16)


if __name__ == "__main__":
	# quick smoke test: connect, read battery, beep once
	async def _demo():
		async with Pavlok() as dev:
			print("battery:", await dev.battery(), "%")
			await dev.beep(5)
			await dev.vibrate(5)
			await dev.shock(3)

	asyncio.run(_demo())
