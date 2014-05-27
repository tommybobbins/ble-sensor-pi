#!/usr/bin/env python
# Michael Saunby. April 2013   
# 
# Read temperature from the TMP006 sensor in the TI SensorTag 
# It's a BLE (Bluetooth low energy) device so using gatttool to
# read and write values. 
#
# Usage.
# sensortag_test.py BLUETOOTH_ADR
#
# To find the address of your SensorTag run 'sudo hcitool lescan'
# You'll need to press the side button to enable discovery.
#
# Notes.
# pexpect uses regular expression so characters that have special meaning
# in regular expressions, e.g. [ and ] must be escaped with a backslash.
#

import pexpect
import sys
import time

def floatfromhex(h):
    t = float.fromhex(h)
    if t > float.fromhex('7FFF'):
        t = -(float.fromhex('FFFF') - t)
        pass
    return t

def baro(self,v):
    global barometer
    global datalog
    rawT = (v[1]<<8)+v[0]
    rawP = (v[3]<<8)+v[2]
    (temp, pres) =  self.data['baro'] = barometer.calc(rawT, rawP)
    self.data['time'] = long(time.time() * 1000);
    print "BARO", temp, pres



# This algorithm borrowed from 
# http://processors.wiki.ti.com/index.php/SensorTag_User_Guide#Gatt_Server
# which most likely took it from the datasheet.  I've not checked it, other
# than noted that the temperature values I got seemed reasonable.
#
def calcTmpTarget(objT, ambT):
    m_tmpAmb = ambT/128.0
    Vobj2 = objT * 0.00000015625
    Tdie2 = m_tmpAmb + 273.15
    S0 = 6.4E-14            # Calibration factor
    a1 = 1.75E-3
    a2 = -1.678E-5
    b0 = -2.94E-5
    b1 = -5.7E-7
    b2 = 4.63E-9
    c2 = 13.4
    Tref = 298.15
    S = S0*(1+a1*(Tdie2 - Tref)+a2*pow((Tdie2 - Tref),2))
    Vos = b0 + b1*(Tdie2 - Tref) + b2*pow((Tdie2 - Tref),2)
    fObj = (Vobj2 - Vos) + c2*pow((Vobj2 - Vos),2)
    tObj = pow(pow(Tdie2,4) + (fObj/S),.25)
    tObj = (tObj - 273.15)
    print "%.2f C" % tObj


class Barometer:

# Ditto.
# Conversion algorithm for barometer temperature
# 
#  Formula from application note, rev_X:
#  Ta = ((c1 * Tr) / 2^24) + (c2 / 2^10)
#
#  c1 - c8: calibration coefficients the can be read from the sensor
#  c1 - c4: unsigned 16-bit integers
#  c5 - c8: signed 16-bit integers
#

    def calcBarTmp(self, raw_temp):
        c1 = self.m_barCalib.c1
        c2 = self.m_barCalib.c2
        val = long((c1 * raw_temp) * 100)
        temp = val >> 24
        val = long(c2 * 100)
        temp += (val >> 10)
        return float(temp) / 100.0


# Conversion algorithm for barometer pressure (hPa)
# 
# Formula from application note, rev_X:
# Sensitivity = (c3 + ((c4 * Tr) / 2^17) + ((c5 * Tr^2) / 2^34))
# Offset = (c6 * 2^14) + ((c7 * Tr) / 2^3) + ((c8 * Tr^2) / 2^19)
# Pa = (Sensitivity * Pr + Offset) / 2^14
#
    def calcBarPress(self,Tr,Pr):
        c3 = self.m_barCalib.c3
        c4 = self.m_barCalib.c4
        c5 = self.m_barCalib.c5
        c6 = self.m_barCalib.c6
        c7 = self.m_barCalib.c7
        c8 = self.m_barCalib.c8
    # Sensitivity
        s = long(c3)
        val = long(c4 * Tr)
        s += (val >> 17)
        val = long(c5 * Tr * Tr)
        s += (val >> 34)
    # Offset
        o = long(c6) << 14
        val = long(c7 * Tr)
        o += (val >> 3)
        val = long(c8 * Tr * Tr)
        o += (val >> 19)
    # Pressure (Pa)
        pres = ((s * Pr) + o) >> 14
        return float(pres)/100.0
    

    class Calib:

        # This works too
        # i = (hi<<8)+lo        
        def bld_int(self, lobyte, hibyte):
            return (lobyte & 0x0FF) + ((hibyte & 0x0FF) << 8)
        
        def __init__( self, pData ):
            self.c1 = self.bld_int(pData[0],pData[1])
            self.c2 = self.bld_int(pData[2],pData[3])
            self.c3 = self.bld_int(pData[4],pData[5])
            self.c4 = self.bld_int(pData[6],pData[7])
            self.c5 = tosigned(self.bld_int(pData[8],pData[9]))
            self.c6 = tosigned(self.bld_int(pData[10],pData[11]))
            self.c7 = tosigned(self.bld_int(pData[12],pData[13]))
            self.c8 = tosigned(self.bld_int(pData[14],pData[15]))
            

    def __init__(self, rawCalibration):
        self.m_barCalib = self.Calib( rawCalibration )
        return

    def calc(self,  rawT, rawP):
        self.m_raw_temp = tosigned(rawT)
        self.m_raw_pres = rawP # N.B.  Unsigned value
        bar_temp = self.calcBarTmp( self.m_raw_temp )
        bar_pres = self.calcBarPress( self.m_raw_temp, self.m_raw_pres )
        return( bar_temp, bar_pres)


#      # fetch barometer calibration
#      tag.char_write_cmd(0x4f,0x02)
#      rawcal = tag.char_read_hnd(0x52)
#      barometer = Barometer( rawcal )
#      # enable barometer
#      tag.register_cb(0x4b,cbs.baro)
#      tag.char_write_cmd(0x4f,0x01)
#      tag.char_write_cmd(0x4c,0x0100)


bluetooth_adr = sys.argv[1]
tool = pexpect.spawn('gatttool -b ' + bluetooth_adr + ' --interactive')
tool.expect('.*\[LE\]>', timeout=600)
print "Preparing to connect. You might need to press the side button..."
tool.sendline('connect')
# test for success of connect
# tool.expect('\[CON\].*>')
# Alternative test for success of connect
tool.expect('Connection successful.*\[LE\]>')
tool.sendline('char-write-cmd 0x4f 0x02')
tool.expect('\[LE\]>')
time.sleep(1)
while True:
    tool.sendline('char-read-hnd 0x52')
    tool.expect('descriptor: .*') 
    rval = tool.after.split()
    objT = floatfromhex(rval[2] + rval[1])
    ambT = floatfromhex(rval[4] + rval[3])
    #print rval
    calcTmpTarget(objT, ambT)
    time.sleep(100)


