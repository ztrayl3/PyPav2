# PyPav2

A simple python module for the [Pavlok 2](https://www.pavlok.com) habit breaking device. The product was released with an API that utilizes a web service, but this module directly connects to the device via Bluetooth Low Energy (BLE). While the module is essentially a wrapper around the linux gatttool, the code allows for very simple usage of the Pavlok 2 device.

Specifically, this project began as a way to implement the Pavlok 2 as a viable and cost effective alternative fear conditioning tool in behavioral psychology. An easy python interface, convenient attachment to the subject, and effective shock elliciting allow it to potentially serve a purpose in psychology research as well as consumer use.

**As of January 2020, the Pavlok 2 device and this code are in use for a psychological study at Louisiana State University testing the efficacy of the device in fear conditioning studies.**

For more information on this project and the Pavlok device's inner workings, please check out the project's [wiki](https://github.com/ztrayl3/PyPav2/wiki), Becky Stern's wonderfully useful [Pavlok Teardown](https://beckystern.com/2020/01/28/pavlok-teardown/), and of course the [Pavlok official website](https://pavlok.com/)

## Requirements:
- The module has been tested on both Python 2.7.13 and Python 3.5.3
- Modules necessary: pexpect, math, datetime
- Gatttool (bluetooth low energy tool, standard in Ubuntu with Bluez, requires a BLE capable device)
*Please note that this software has only been tested in Linux and with the Bluez tools, Windows may eventually have compatability but not in the near future*

## Stimulus Arguments:
- level: an integer from 0 to 10
- count: number of times to repeat stimulus 0 - 7
- duration_on: stimulus duration in seconds (max 10 seconds, minimum .11 seconds) *
- gap: time in milliseconds between simulus repetitions (see duration_on restrictions) *
- example: device.beep(10, 2, 1, 1)

\* *duration_on* and *gap* only apply to the beep and vibrate functions, shock does not allow for repetition beyond one shock natively. Shock repetition *can* be performed outside of the function, though there is a 700ms delay between each shock.

### Usage
    from PyPav2 import Pavlok
    device = Pavlok(mac="mac:address:of:your:device")
    
    device.beep(5)
    device.shock(2, count=2)
    device.beep(10, count=1, duration_on=1.5)
    device.vibrate(10, count=2, duration_on=1, gap=.5)

    device.button_assign("vibrate", 7, count=2, duration_on=.5, gap=.5)

## Clock Arguments:
- sync: boolean value to synchronize Pavlok 2 clock with computer's UTC time
- utcd: integer difference of local timezone from UTC (ex: US Central time = -5)
- dst: boolean value to adjust for US daylight savings time

### Usage
    device.clock()  # return time from Pavlok 2 on-board clock
    device.clock(sync=True)  # synchronize clock to UTC time on computer
    device.clock(sync=True, utcd=-5, dst=False)  # synchronize clock to local time, denoted by UTC difference and daylight savings time

## Miscellaneous Functions:
    device.battery()  # returns integer battery percentage
    device.vibe_count()  # returns integer tally of vibrate calls
    device.beep_count()  # returns integer tally of beep calls
    device.shock_count()  # returns integer tally of shock calls

## On the way (hopefully):
- a button count function
- LED control
- accelerometer/gyroscope access
- alarm configuration
