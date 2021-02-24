#!/usr/bin/env python3
import sys
import argparse
import time
import socket

class scpi (object):
    """SCPI class used to access Red Pitaya over an IP network."""
    delimiter = '\r\n'

    def __init__(self, host, timeout=None, port=5000):
        """Initialize object and open IP connection.
        Host IP should be a string in parentheses, like '192.168.1.100'.
        """
        self.host    = host
        self.port    = port
        self.timeout = timeout

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if timeout is not None:
                self._socket.settimeout(timeout)

            self._socket.connect((host, port))

        except socket.error as e:
            print('SCPI >> connect({:s}:{:d}) failed: {:s}'.format(host, port, e))

    def __del__(self):
        if self._socket is not None:
            self._socket.close()
        self._socket = None

    def close(self):
        """Close IP connection."""
        self.__del__()

    def rx_txt(self, chunksize = 4096):
        """Receive text string and return it after removing the delimiter."""
        msg = ''
        while 1:
            chunk = self._socket.recv(chunksize + len(self.delimiter)).decode('utf-8') # Receive chunk size of 2^n preferably
            msg += chunk
            if (len(chunk) and chunk[-2:] == self.delimiter):
                break
        return msg[:-2]


    def tx_txt(self, msg):
        """Send text string ending and append delimiter."""
        return self._socket.send((msg + self.delimiter).encode('utf-8'))

    def txrx_txt(self, msg):
        """Send/receive text string."""
        self.tx_txt(msg)
        return self.rx_txt()


    def err_c(self):
        """Error count."""
        return rp.txrx_txt('SYST:ERR:COUN?')

    def err_c(self):
        """Error next."""
        return rp.txrx_txt('SYST:ERR:NEXT?')

def readByteArray():
    buf = rp_s._socket.recv(1)
#    print(buf.decode('utf-8'))

    buf = rp_s._socket.recv(1)
    digits_in_byte_count = int(buf)

    buf = rp_s._socket.recv(digits_in_byte_count)
#    print(buf.decode('utf-8'))
    byte_count = int(buf)

    buff = []
    while len(buff) != byte_count:
        data = rp_s._socket.recv(16)
        buff.extend([data[i:i+1] for i in range(0, len(data), 1)])
#        print(len(buff))
    return buff

parser = argparse.ArgumentParser(description='Setup Red Pitaya')
parser.add_argument('-td', '--trigDelay', type=int, default=1, help='trigger delay samples (default is 1)')
args = parser.parse_args()

rp_s = scpi("192.168.10.11")
#print(args.trigDelay)

#rp_s.tx_txt('ACQ:RST')

rp_s.tx_txt('ACQ:AVG OFF')
rp_s.tx_txt('ACQ:DATA:UNITS RAW')
rp_s.tx_txt('ACQ:DATA:FORMAT BIN')
rp_s.tx_txt('ACQ:DEC 1')
rp_s.tx_txt('ACQ:TRIG:LEV 500 mV')
rp_s.tx_txt('ACQ:TRIG:DLY ' + str(args.trigDelay))
rp_s.tx_txt('ACQ:SOUR1:COUP DC')
rp_s.tx_txt('ACQ:SOUR2:COUP DC')

while 1:
    rp_s.tx_txt('ACQ:START')
    rp_s.tx_txt('ACQ:TRIG EXT_PE')

    while 1:
       rp_s.tx_txt('ACQ:TRIG:STAT?')
       if rp_s.rx_txt() == 'TD':
            break
    #print('Triggered')

    rp_s.tx_txt('ACQ:SOUR1:DATA:OLD:N? 512')
    buf1 = b''.join(readByteArray())
    rp_s.tx_txt('ACQ:SOUR2:DATA:OLD:N? 512')
    buf2 = b''.join(readByteArray())
    bufTotal = b''.join([buf1,buf2])
    sys.stdout.buffer.write(bufTotal)
