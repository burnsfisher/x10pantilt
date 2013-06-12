# /* Copyright (C) 2010 Michael LeMay
#  * 
#  * This program is free software; you can redistribute it and/or modify
#  * it under the terms of the GNU General Public License as published by
#  * the Free Software Foundation; either version 2 of the License, or
#  * (at your option) any later version.
#  *
#  * This program is distributed in the hope that it will be useful,
#  * but WITHOUT ANY WARRANTY; without even the implied warranty of
#  * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  * GNU General Public License for more details.
#  *
#  * You should have received a copy of the GNU General Public License along
#  * with this program; if not, write to the Free Software Foundation, Inc.,
#  * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#  * 
#  * Communications driver for X10 CM19A RF home automation transceiver
#  */

import usb.core
import usb.util
import sys
import threading
import traceback
import os
import time

DEBUG = 0

# /**********************/
# /*** X10 OPERATIONS ***/
# /**********************/

# /* Bounds of X10 house codes */
HOUSE_MIN = 'a'
HOUSE_MAX = 'p'

# /* Bounds of X10 unit codes */
UNIT_MIN = 1
UNIT_MAX = 16

# /**
#  * House codes
#  */
HouseCodes = {
	'a' : 0x060, 'b' : 0x070, 'c' : 0x040, 'd' : 0x050,
	'e' : 0x080, 'f' : 0x090, 'g' : 0x0A0, 'h' : 0x0B0,
	'i' : 0x0E0, 'j' : 0x0F0, 'k' : 0x0C0, 'l' : 0x0D0,
	'm' : 0x000, 'n' : 0x010, 'o' : 0x020, 'p' : 0x030
}

def houseCodeToChar(code):
    for k, v in HouseCodes.items():
        if code == v:
            return k
    raise ValueError('Unrecognized house code: ' + str(code))

# /**
#  * Translate house code to octet necessary for 2nd byte in Pan'n'Tilt commands
# */
HouseCodeToCamCode = {
    HouseCodes['a'] : 0x090,
    HouseCodes['b'] : 0x0A0,
    HouseCodes['c'] : 0x070,
    HouseCodes['d'] : 0x080,
    HouseCodes['e'] : 0x0B0,
    HouseCodes['f'] : 0x0C0,
    HouseCodes['g'] : 0x0D0,
    HouseCodes['h'] : 0x0E0,
    HouseCodes['i'] : 0x010,
    HouseCodes['j'] : 0x020,
    HouseCodes['k'] : 0x0F0,
    HouseCodes['l'] : 0x000,
    HouseCodes['m'] : 0x030,
    HouseCodes['n'] : 0x040,
    HouseCodes['o'] : 0x050,
    HouseCodes['p'] : 0x060
}

def isCamCode(code):
    return (code & ~0x0FF) != 0

# /**
#  * Unit codes
#  */
UnitCodes = [
    0x0000, 0x0010, 0x0008, 0x0018, 0x0040, 0x0050, 0x0048, 0x0058,
    0x0400, 0x0410, 0x0408, 0x0418, 0x0440, 0x0450, 0x0448, 0x0458
]

# fancy way to convert a unit code to a unit number:
def unitCodeToInt(code):
    unit = ((code >> 7) & 0x08)
    unit |= ((code >> 4) & 0x04)
    unit |= ((code >> 2) & 0x02)
    unit |= ((code >> 4) & 0x01)
    return unit+1

# /**
#  * Command codes
#  */
CmdCodes = {
#	/* Standard 5-byte commands: */
	'CMD_ON'      : 0x000, # /* Turn on unit */
	'CMD_OFF'     : 0x020, # /* Turn off unit */
	'CMD_DIM'     : 0x098, # /* Dim lamp */
	'CMD_BRIGHT'  : 0x088, # /* Brighten lamp */
#	/* Pan'n'Tilt 4-byte commands: */
	'CMD_UP'      : 0x0762,
	'CMD_RIGHT'   : 0x0661,
	'CMD_DOWN'    : 0x0863,
	'CMD_LEFT'    : 0x0560,
}

CmdCodeDict = {
    '+' : 'CMD_ON',
    '-' : 'CMD_OFF',
    'u' : 'CMD_UP',
    'd' : 'CMD_DOWN',
    'l' : 'CMD_LEFT',
    'r' : 'CMD_RIGHT',
    'b' : 'CMD_BRIGHT',
    's' : 'CMD_DIM'
}

def parseCmd(c):
    code = CmdCodeDict.get(c)
    if code == None:
         raise ValueError('Invalid command code: ' + str(c))

    return code

def codeToCmd(code):
    for k, v in CmdCodes.items():
        if code == v:
            return k
    raise ValueError('Unrecognized command code: ' + str(code))

def cmdToChar(cmd):
    for k, v in CmdCodeDict.items():
        if cmd == v:
            return k
    raise ValueError('Unrecognized command: ' + str(cmd))

class X10HACommand:
    def __init__(self, cmd, house, unit):
        self.cmd = cmd
        self.house = house.lower()
        self.unit = unit

        if (self.house not in HouseCodes):
            raise ValueError('Invalid house code: ' + self.house)

        if not ((UNIT_MIN <= unit) and (unit <= UNIT_MAX)):
            raise ValueError('Invalid unit code: ' + self.unit)

    def xmit(self, outEp):
        houseCode = HouseCodes[self.house]
        unitCode = UnitCodes[self.unit-1]
        cmdCode = CmdCodes[self.cmd]

        cmd = []
        if isCamCode(cmdCode):
            cmd += [CAM_CMD_PFX]
            cmd += [(cmdCode >> 8) | HouseCodeToCamCode[houseCode]]
            cmd += [cmdCode & 0x0FF]
            cmd += [houseCode]
        else:
            cmd += [NORM_CMD_PFX]
            cmd += [(unitCode >> 8) | houseCode]
            cmd += [0x0FF & ~cmd[1]]
            cmd += [(unitCode & 0x0FF) | cmdCode]
            cmd += [0x0FF & ~cmd[3]]

        if DEBUG:
            sys.stderr.write('Sending: ' + str(cmd) + '\n')

        outEp.write(cmd, 10000)

    def tostr(self):
        if isCamCode(CmdCodes[self.cmd]):
            return cmdToChar(self.cmd) + self.house
        else:
            return cmdToChar(self.cmd) + self.house + str(self.unit)

def X10Send(inp, outEp):
    if DEBUG:
        sys.stderr.write('X10Send called with buffer:' + inp + ' ' + str(len(inp)) + '\n')

    # /* check for empty buffer */
    if (len(inp) == 0):
        return

    # // shortest command is pan/tilt (2 bytes + newline)
    if (len(inp) < 3):
        raise ValueError('Command is too short, ignoring: ' + str(len(inp)))

    if (len(inp) > MAX_CMD_LEN):
        raise ValueError('Invalid input command length:' + str(len(inp)))

    i = 0
    cmd = parseCmd(inp[i])
    i = i + 1

    if DEBUG:
        sys.stderr.write('got command ' + cmd + '\n')

    house = inp[i]
    i = i + 1
        
    if DEBUG:
        sys.stderr.write('house code: ' + house + '\n');

    unit = 0

    if (i < len(inp)):
        c = inp[i]
        i = i + 1

        if (ord(c) < ord('0')) or (ord(c) > ord('9')):
            raise ValueError('Malformed command, illegal digit #1: ' + c)
        else:
            unit = ord(c) - ord('0')

        if (i < len(inp)):
            c = inp[i]
            i = i + 1
            if (ord(c) < ord('0')) or (ord(c) > ord('9')):
                raise ValueError('Illegal digit #2: ' + c)
            else:
                unit *= 10
                unit += ord(c) - ord('0')

        if DEBUG:
            sys.stderr.write('unit = ' + str(unit) + '\n')

    else:
        if ((cmd == 'CMD_ON') or (cmd == 'CMD_OFF')):
            raise ValueError('On and off commands require a unit number')


    cmd = X10HACommand(cmd, house, unit)
    cmd.xmit(outEp)

# Normal command length
NORM_CMD_LEN = 5
# Pan'n'Tilt command length
CAM_CMD_LEN = 4
# Larger of the two lengths, used for allocating buffers
MAX_CMD_LEN = NORM_CMD_LEN

# Prefix for all normal commands
NORM_CMD_PFX = 0x020
# Prefix for all Pan'n'Tilt commands
CAM_CMD_PFX = 0x014

ACK_LEN = 1
ACK = 0x0FF

Done = False

class ReceiveThread(threading.Thread):
    def __init__(self, inEp, outEp):
        threading.Thread.__init__(self)
        self.inEp = inEp
        self.outEp = outEp
        self.lastCmd = ''
        self.lastCmdTime = 0

    def run(self):
        while not Done:
            self.listen()

    def procCmd(self, curCmd):
        curTm = time.time()
        if curCmd == self.lastCmd:
            if (curTm - self.lastCmdTime) < 0.6:
                return
        self.lastCmd = curCmd
        self.lastCmdTime = curTm
        sys.stdout.write(curCmd + '\n')
        sys.stdout.flush()

    def procNormCmd(self, buf):
        unitCode = (((buf[0] & 0x0F) << 8) | (buf[2] & ~CmdCodes['CMD_OFF']))
        houseCode = (buf[0] & 0x0F0)
        cmdCode = (buf[2] & CmdCodes['CMD_OFF'])

        curCmd = X10HACommand(codeToCmd(cmdCode), houseCodeToChar(houseCode), unitCodeToInt(unitCode)).tostr()
        self.procCmd(curCmd)

    def procCamCmd(self, buf):
        cmdCode = (((buf[0] & 0x0F) << 8) | buf[1])
        houseCode = buf[2]
        unitCode = UnitCodes[0]
        
        curCmd = X10HACommand(codeToCmd(cmdCode), houseCodeToChar(houseCode), unitCodeToInt(unitCode)).tostr()
        self.procCmd(curCmd)

    def listen(self):
        try:
            dat = self.inEp.read(MAX_CMD_LEN)
            if dat[0] == NORM_CMD_PFX:
                self.procNormCmd(dat[1:])
            elif dat[0] == CAM_CMD_PFX:
                self.procCamCmd(dat[1:])
        except usb.USBError:
            pass # Catch timeout exception. Unfortunately, other exception types are not distinguished, so we just hope they don't occur.
        except:
            traceback.print_exc()

# Initialize CM19A so it recognizes signals from the CR12A or CR14A remote
def init_remotes(outEp):
    cr12init1 = [ 0x020, 0x034, 0x0cb, 0x058, 0x0a7 ]
    cr12init2 = [ 0x080, 0x001, 0x000, 0x020, 0x014 ]
    cr12init3 = [ 0x080, 0x001, 0x000, 0x000, 0x014, 0x024, 0x020, 0x020 ]

    writeRes = outEp.write(cr12init1)
    writeRes = outEp.write(cr12init2)
    writeRes = outEp.write(cr12init3)

sys.stderr.write('Attempting to remove ati-remote module (if necessary; just ignore any errors it produces)...\n')
os.system('rmmod ati-remote')

# Locate X10 CM19A:
Dev = usb.core.find(idVendor=0x0bc7, idProduct=0x0002)
# bConfigurationValue = 1
#   bInterfaceNumber = 0, bAlternateSetting = 0
#     bEndpointAddress = 129
#     bEndpointAddress = 2

if Dev is None:
    raise ValueError('Device not found')

sys.stderr.write('Discovered X10 CM19A.  Attempting to set its configuration...\n')

# select first configuration:
try:
    Dev.set_configuration()
except:
    sys.stderr.write('Failed to set configuration.  Are you logged in as root?\n')
    raise

# find output endpoint:
OutEp = usb.util.find_descriptor(
        Dev.get_interface_altsetting(),
        custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
    )

sys.stderr.write('Connected to output endpoint: ' + str(OutEp.bEndpointAddress) + '\n')

# find input endpoint:
InEp = usb.util.find_descriptor(
        Dev.get_interface_altsetting(),
        custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
    )

sys.stderr.write('Connected to input endpoint: ' + str(InEp.bEndpointAddress) + '\n')

init_remotes(OutEp)

rcvThr = ReceiveThread(InEp, OutEp)
rcvThr.start()

if __name__ == '__main__':
    try:
        while True:
            line = sys.stdin.readline()
            if len(line)>0:
                X10Send(line[0:len(line)-1], OutEp)
            time.sleep(0.1)
    except:
        traceback.print_exc()
        sys.stderr.write('Exiting X10 CM19A driver.\n')
        Done = True
