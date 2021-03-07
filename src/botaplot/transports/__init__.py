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
        self.address = address
        self.port = port
        self._file = None
        self.sock = None
        self._file = None

    def __str__(self):
        return "<TelnetTransport to %s:%d>" % (self.address, self.port)

    @property
    def file(self):
        if self._file is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10.0)
            self.sock.connect((self.address, self.port))
            self._file = self.sock.makefile("rwb")
            header = self._file.readline()
            if "Smoothie command shell" not in header.decode('ascii'):
                raise IOError("Unrecognized protocol header: %s" % header)
        return self._file

    def readline(self):
        try:
            line = self.file.readline()
        except socket.timeout:
            self._file = None
            self.sock.close()
            self.sock = None
            raise
        if line.startswith(">".encode('ascii')):  # Strip prompt
            line = line[1:]
        return line

    def write(self, bytestring):
        try:
            written = self.file.write(bytestring)
            self.file.flush()
        except socket.timeout:
            self._file = None
            self.sock.close()
            self.sock = None
            raise
        return written


class SerialTransport(BaseTransport):
    """Transport for gcode/hpgl over the serial wire"""

    def __init__(self, port, speed=115200):
        """The port is the path to the serial port."""
        self.portname = port
        self.speed = speed
        self._file = None

    @property
    def file(self):
        if self._file is None:
            self._file = serial.Serial(self.portname, self.speed, timeout=30)
        return self._file

    def write(self, bytestring: bytes):
        try:
            return super().write(bytestring)
        except:
            self._file.close()
            self._file = None
            raise


    def readline(self):
        try:
            return super().readline()
        except:
            self._file.close()
            self._file = None
            raise