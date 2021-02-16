import socket
import serial

class BaseTransport(object):
    def readline(self, *args, **kw):
        return self.file.readline(*args, **kw)

    def write(self, *args, **kw):
        return self.file.write(*args, **kw)

class TelnetTransport(BaseTransport):
    """Simple Gcode over telnet. Mostly just for smoothie."""

    def __init__(self, address, port=23):
        """The port is the path to the serial port."""
        self.portname = address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((address, port))
        self.file = self.sock.makefile("rwb")
        header = self.file.readline()
        if "Smoothie command shell" not in header.decode('ascii'):
            raise IOError("Unrecognized protocol header: %s" % header)

    def readline(self):
        line = self.file.readline()
        if line.startswith(">".encode('ascii')):  # Strip prompt
            line = line[1:]
        return line

    def write(self, bytestring):
        written = self.file.write(bytestring)
        self.file.flush()
        return written


class SerialTransport(BaseTransport):
    """Transport for gcode/hpgl over the serial wire"""

    def __init__(self, port, speed=115200, ):
        """The port is the path to the serial port."""
        self.portname = port
        self.file = serial.Serial(port, speed, timeout=30)
