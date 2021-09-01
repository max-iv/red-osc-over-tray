#!/usr/bin/env python3
import pyvisa as visa
import time
import random
import sys
import struct

timePos = 250
timeRef = 10
loopDelay = 0.5
rfFreq = 99.5
sampleRate = 1000.0
iTraceOffset = 0.000;
qTraceOffset = 0.000;
mixer6OrderCal100mV = 0.0 #0.0078125
bunchCurrentTo100mV = 1.8466 #1.02

rm = visa.ResourceManager('@py')
rp = rm.open_resource('TCPIP::{}::{}::SOCKET'.format('192.168.10.10', 5025), read_termination = '\n')
rp.write("*RST")
rp.write("CHAN1:STAT ON;")
rp.write("CHAN1:POS 0;")
rp.write("CHAN1:COUP DC;")
rp.write("CHAN1:SCAL 0.05;")
rp.write("CHAN1:POL NORM;")

rp.write("CHAN2:STAT ON;")
rp.write("CHAN2:POS 0;")
rp.write("CHAN2:COUP DC;")
rp.write("CHAN2:SCAL 0.02;")
rp.write("CHAN2:POL NORM;")

rp.write("CHAN4:STAT ON;")
rp.write("CHAN4:POS 0;")
rp.write("CHAN4:COUP DC;")
rp.write("CHAN4:SCAL 1.0;")
rp.write("CHAN4:POL NORM;")

rp.write("TIM:SCAL 200e-9;")
rp.write("TIM:POS " + str(timePos) + "e-9;")
rp.write("TIM:REF " + str(timeRef) + ";")

rp.write("TRIG1:SOUR CHAN4;")
rp.write("TRIG1:EDGE:SLOP POS;")
rp.write("TRIG1:MODE NORM;")
rp.write("TRIG1:LEV4:VAL 1.0;")
rp.write("ACQ:SRAT " + str(sampleRate) + "e6;")
rp.write("FORM:DATA REAL;");
rp.write("FORM:BPAT BIN;");

time.sleep(1.0)
sampleRate = float(rp.query("ACQ:SRAT?")) / 1e6
#print(sampleRate)
while 1:
    startTime = time.time()
    rp.write("SING;*OPC;")

    traceI = rp.query_binary_values('CHAN1:WAV1:DATA?', datatype='f', is_big_endian=False);
    traceQ = rp.query_binary_values('CHAN2:WAV1:DATA?', datatype='f', is_big_endian=False);
    npts = len(traceI)
    for ii in range(0,npts):
        traceI[ii] = (traceI[ii] - iTraceOffset) * 10.0
        sign = 1.0
        if traceI[ii] < 0:
            sign = -1.0
            traceI[ii] = -traceI[ii]
        traceI[ii] = sign * (traceI[ii] + mixer6OrderCal100mV * (traceI[ii] ** 6))
#6dB splitter in front of Q channel
        traceQ[ii] = (traceQ[ii] - qTraceOffset) * 20.0
        sign = 1.0
        if traceQ[ii] < 0:
            sign = -1.0
            traceQ[ii] = -traceQ[ii]
        traceQ[ii] = sign * (traceQ[ii] + mixer6OrderCal100mV * (traceQ[ii] ** 6))
    bufI = []
    bufQ = [] 
    for ibunch in range(0,176):
        isampleStart = round((ibunch + 0.0) * sampleRate / rfFreq)
        isampleStop  = round((ibunch + 1.0) * sampleRate / rfFreq)
        bunchI = 0.0
        bunchQ = 0.0
        nsamples = 0.0
        for isample in range(isampleStart, isampleStop + 1):
            bunchI = bunchI + traceI[isample]
            bunchQ = bunchQ + traceQ[isample];
            nsamples = nsamples + 1.0;
        bunchI = bunchCurrentTo100mV * bunchI / nsamples;
        bunchQ = bunchCurrentTo100mV * bunchQ / nsamples;
        bufI.append(struct.pack("f", bunchI))
        bufQ.append(struct.pack("f", bunchQ))
    bufTotal = b''.join([b''.join(bufI),b''.join(bufQ)])
    endTime = time.time();
    while (endTime - startTime) <= (loopDelay + 1.0 * random.uniform(-0.001, 0.001)):
        endTime = time.time()
    sys.stdout.buffer.write(bufTotal)
#    print(endTime - startTime)

rp.close()
