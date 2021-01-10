class SimpleAsciiProtocol(object):
    """Protocol that sends pen commands with newlines between"""

    def __init__(self, wait_for_ok=True):
        self.wait_for_ok = wait_for_ok

    def plot(self, cmds_source, transport):
        for cmd in cmds_source:
            print("Sending %s" % cmd)
            transport.write(("%s\n" % cmd).encode('ascii'))
            if self.wait_for_ok:
                response = transport.readline().decode('ascii').strip()
                print("Got response", response)
                if response is None or not response or "OK" not in response.upper():
                    print("Response: '%s'" % response)
                    raise IOError("Invalid response from upstream plotter.")

