# PyPav2

A simple python module for the [Pavlok 2](https://www.pavlok.com) habit breaking device. The product was released with an API that utilizes a web service, but this module directly connects to the device via Bluetooth Low Energy (BLE). While the module is essentially a wrapper around the linux gatttool, the code allows for very simple usage of the Pavlok 2 device.

Specifically, this project began as a way to implement the Pavlok 2 as a viable and cost effective alternative fear conditioning tool in behavioral psychology. An easy python interface, convenient attachment to the subject, and effective shock elliciting allow it to potentially serve a purpose in psychology research as well as consumer use.

**As of January 2020, the Pavlok 2 device and this code are in use for a psychological study at Louisiana State University testing the efficacy of the device in fear conditioning studies.**

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

## Usage
    from pavlok import Pavlok
    device = Pavlok(mac="mac:address:of:your:device")
    
    device.beep(5)
    device.beep(10, count=1, duration_on=1.5)
    device.vibrate(10, count=2, duration_on=1, gap=.5)
    
    device.shock(5)
    device.shock(5, count=1)

# Reverse Engineering the Pavlok 2

This all began as a personal project in spite towards my lab's shock device. We utilise a Biopac STM100C Programmable Stimulator Module alongside a Biopac STMISOC Stimulation Isolation Adapter. While these devices are incredibly powerful and precise, for some laboratories they may be prohibitively expensive, with just the STMISOC running around $450. My P.I. had backed the Pavlok on Kickstarter for as an affective psychologist he was interested in the device's potential in research. After some time, I picked up the project as a programming challenge with the potential for a study and took it from there.

The officialy Pavlok API exists, but it does not allow direct connection and control of the device. The entire process is routed through an online service, and that wouldn't do. Since the officialy API is web hosted, there was no documentation for the functioning of the device. Thanks to a piece of software called [btlejuice](https://github.com/DigitalSecurity/btlejuice) and some spare Raspberry Pi's I had lying around, I was able to effectively perform a MITM "attack" on my phone and log all the packets running from the Pavlok app to the device itself.

The device communicates with its host via the BLE GATT protocol, wherein specific "handles" are assigned to functions in the device. Packets are more-or-less sent to these handle addresses and the device executes the command if it fits the correct syntax (I am no expert on GATT, but for further reading, see [this page](https://www.bluetooth.com/specifications/gatt/). While some GATT attributes have standardized handles (such as battery and firmware), most are proprietary and not advertised by the Pavlok device. However, thanks to the android tool [nRF connect](https://play.google.com/store/apps/details?id=no.nordicsemi.android.mcp&hl=en_US), I was able to see every attribute open to recieving packets on the Pavlok, all of their handles, and *with human readable names*. From there, I went back to my MITM setup and executed every function the official Pavlok app had, and at every intensity level and possible configuration. With all possible data logged between the app and the device, I went to breaking down the packets.

Not every part of the communication protocol is figured out, as I am again no expert in any of this, but for better or for worse a solid pattern exists for all stimuli commands. Data is formatted as "8(number of repetitions)0c(level of intensity)(duration_on)(gap between repetitions)", all values being integers converted to hexidecimal values. The "8" and the "0c" are still a work in progress. Shock only utilises count and level, for some reason sending a much shorter packet than the other stimuli. Other handles such as "Button Assign" and "Clock" have specific formats as well, but those were a bit easier to figure out by just figitting with settings in the Pavlok app and seeing what it communicated to the device. 

What was the most odd was the existence of a duration option and a gap between repetitions, as these features are not available in the app. In fact, I only figured out their use by randomly assigning values and seeing what would happen. Furthermore, they don't seem to accept values the same way as the other fields, and I couldn't quite find a pattern. Instead, I sampled every level (0-63, in hex) with as much stopwatch accuracy as I could get with my computer and came up with an exponential regression that rather accurately calculates a time in seconds from a given hex value. The user entered time, in seconds, is fed to the model and the hex value returned is sent to the device.

From there, the PyPav2 module simply offers a python wrapper for a gatttool interface. It establishes a BLE connection with the Pavlok 2 **(pairing your linux computer with the Pavlok may be a bit of a hassle but I got it eventually and it hasn't offered me trouble since)** and then takes human input, converts it to hex packets, and sends it through gatttool to the correct address on the device.

The project has been loads of fun and a great challenge in terms of my computer science abilities. Follow any updates on the progress of our official Pavlok research study on the [Pavlok official subreddit](https://www.reddit.com/r/Pavlok/)! *Please note that this project is in no way funded or supported by the Pavlok company (if only) and is entirely a personal and non-profit endeavor*

Video example using a Raspberry Pi Zero w
https://youtu.be/dpEqDgbgF_0
