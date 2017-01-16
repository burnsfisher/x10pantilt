X10 CM19A Python driver
=======================

by Michael LeMay
Mods to support pan/tilt (Ninja) by Burns Fisher
Further fixes and mods by Burns Fisher

* Please note that we are not affiliated with X10 in any way, nor is this
  driver.
* X10 is a Registered Trademark of X10 Wireless Technology, Inc.
* By using this software you agree to the terms of the license agreement
  contained within the file named LICENSE in the same directory as this file.

This driver supports the X10 CM19A USB RF Transceiver.

Installation
------------

### Microsoft Windows 10
1. [Install Chocolatey](https://chocolatey.org/install)
2. Run the following commands in PowerShell opened as administrator
   * `choco install zadig`
   * `zadig` (with CM19A plugged into computer)
      * Enable "Options -> List All Devices"
      * Look for a device called "USB Transceiver" with USB ID `0BC7 0002`
      * Select libusb-win32 driver
      * Press "Replace Driver"
      * Exit Zadig
   * `choco install python`
3. Run the following commands in PowerShell opened as normal user
   * `pip3 install pyusb`
   * `python pycm19a.py` (see "Command format" section below)

### Linux
1. Uninstall any version of pyusb that may already be installed on your
   computer.  Currently, Linux distributions often include a version of pyusb
   that is too old, and it conflicts with the new one.
2. Install pyusb 1.0 as described on http://pyusb.sf.net.
3. Plugin the X10 CM19A transceiver
4. Grant access to the appropriate USB device to your preferred user account
   * Execute `sudo lsusb` to list devices.
   * Look for a device with the name "X10 Wireless Technology, Inc. Firecracker
     Interface" and USB ID `0bc7:0002`.
   * Take note of the "Bus" and "Device" IDs.
   * Execute `chmod 600 /dev/bus/usb/<bus ID>/<device ID>` to make the device
     readable and writable by its owner.
   * Execute `chown <user> /dev/bus/usb/<bus ID>/<device ID>` to set your
     preferred user account as the owner of the device.
5. As that user, run `python pycm19a.py` (see "Command format" section below)

Command format (with examples)
------------------------------
You can give a single X10 command (as shown below) on the command line.
Pycm19a will execute that command and exit.  If you put nothing on the
command line, it will read commands from stdin as usual.

Each house code (`<house>`) is a character between `a` and `p`.

Each device number (`<dev>`) is between 1 and 16.

### Basic on/off commands:
`[-+]<house><dev>`

Command | Description
------- | -----------
`-` | off
`+` | on

#### Examples:
* Turn on device C16: `+c16`
* Turn off device D8: `-d8`

### Ninja Pan'n'Tilt commands:
`[udlrc1234]<house>`

Command | Description
------- | -----------
`u` | up
`d` | down
`l` | left
`r` | right
`c` | center
`1` | Position 1
`2` | Position 2
`3` | Position 3
`4` | Position 4

#### Examples:
* Turn camera on housecode D right by one click: `rd`

### Lamp module commands:
`[bs]<house><dev>`

Command | Description
------- | -----------
`b` | brighten
`s` | soften

#### Examples:
* Brighten lamp on C3: `bc3` (may need to be preceded by `+c3`)

### Miscellaneous commands:

Command | Description
------- | -----------
`x` | exit quietly

Acknowledgments
---------------
Special thanks to Neil Cherry of the Linux-HA project for giving
me some code to jump off of while developing the Linux Kernel driver
that preceded this driver.

Thanks also to the others that have given me bug reports and feedback
on this driver and its ancestors!
