import logging
import time
logger=logging.getLogger(__name__)


class PlotJobCancelled(RuntimeError):
    """Special exception for murdering a plotter job"""
    pass


class SimpleAsciiProtocol(object):
    """Protocol that sends pen commands with newlines between"""

    def __init__(self, wait_for_ok=True):
        self.wait_for_ok = wait_for_ok
        self.paused = True
        self.ready = True
        self.die = False

    def single(self, cmd, transport):
        logger.info("Send cmd:'%s'" % cmd)
        transport.write(cmd.encode('ascii'))
        if self.wait_for_ok:
            response = transport.readline().decode('ascii').strip()
            if response is None or not response or "OK" not in response.upper():
                logger.error("Response: '%s'", response)
                raise IOError("Invalid response from upstream plotter.")

    def plot(self, cmds_source, transport, callback=None):
        self.ready = False
        self.paused = False
        pending_oks = 0
        for i, cmd in enumerate(cmds_source):
            while self.paused and not self.die:
                time.sleep(1)
            if self.die:
                break
            # print("Sending %s" % cmd)
            # print("Callback:", callback, callable(callback))

            if callback is not None and callable(callback):
                try:
                    callback(i, len(cmds_source), cmd)
                except PlotJobCancelled:
                    logger.error("Job cancelled via PlotJobCancelled")
                    break

            pending_oks += 1
            transport.write(("%s\n" % cmd).encode('ascii'))
            if self.wait_for_ok:
                while pending_oks > transport.lookahead:
                    print("Pending OKs:", pending_oks)
                    if self.die:
                        break
                    response = transport.readline().decode('ascii').strip()
                    print("Got response", response)
                    if response is None or not response or "OK" not in response.upper():
                        print("Response: '%s'" % response)
                        raise IOError("Invalid response from upstream plotter.")
                    else:
                        pending_oks -= 1
        self.ready = True  # We're done.

    def rewind(self):
        """Kill the plot and rewind to the beginning"""
        self.die = True


