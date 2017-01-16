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

1. Uninstall any version of pyusb that may already be installed on your
   computer.  Currently, Linux distributions often include a version of pyusb
   that is too old, and it conflicts with the new one.
2. Install pyusb 1.0 as described on http://pyusb.sf.net.
3. Plugin the X10 CM19A transceiver
4. Grant access to the appropriate USB device to your preferred user account
5. As that user, run python pycm19a.py (see "Command format" section below)
6. You can give a single X10 command (as shown below) on the command line.
   Pycm19a will execute that command and exit.  If you put nothing on the
   command line, it will read commands from stdin as usual.

Command format (with examples)
------------------------------

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
