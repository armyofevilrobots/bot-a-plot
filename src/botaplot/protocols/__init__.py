import logging
import time
logger=logging.getLogger(__name__)

class SimpleAsciiProtocol(object):
    """Protocol that sends pen commands with newlines between"""

    def __init__(self, wait_for_ok=True):
        self.wait_for_ok = wait_for_ok
        self.paused = True

    def plot(self, cmds_source, transport, callback=None):
        self.paused = False
        pending_oks = 0
        for i, cmd in enumerate(cmds_source):
            while self.paused:
                time.sleep(1)
            print("Sending %s" % cmd)
            print("Callback:", callback)

            if callback is not None and callable(callback):
                callback(i, len(cmds_source), cmd)
            pending_oks += 1
            transport.write(("%s\n" % cmd).encode('ascii'))
            if self.wait_for_ok:
                while pending_oks > 5:
                    response = transport.readline().decode('ascii').strip()
                    print("Got response", response)
                    if response is None or not response or "OK" not in response.upper():
                        print("Response: '%s'" % response)
                        raise IOError("Invalid response from upstream plotter.")
                    else:
                        pending_oks -= 1

