import time
import unittest
import uuid
from botaplot.models.plot_sender import PlotWorker
from botaplot.models.machine import BotAPlot
from botaplot.protocols import SimpleAsciiProtocol
from botaplot.transports import BaseTransport

class MockTransport(BaseTransport):

    def __init__(self):
        super().__init__()
        self.cmd_count = 0
        self.delay = 0

    def write(self, *args, **kw):
        self.cmd_count += 1

    def readline(self, *args, **kw):
        if self.cmd_count > 0:
            return("OK".encode('ascii'))
        else:
            raise RuntimeError("Asking for response, nothing written.")


class TestPlotSender(unittest.TestCase):

    def setUp(self):
        machine = BotAPlot(MockTransport())
        self.sender = PlotWorker.new(machine)

    def test_dies(self):
        self.assertEqual(self.sender.dead, False)
        self.assertEqual(True, self.sender.kill())
        for i in range(100):
            if self.sender.dead:
                break
            time.sleep(0.01)
        self.assertEqual(self.sender.dead, True)

    def test_cmd_validate(self):
        id = str(uuid.uuid1())
        cmd = f"STATUS[{id}]:foobar"
        matches = self.sender.cmd_match.match(cmd)
        self.assertEqual(id, matches.groupdict()['id'])
        self.assertEqual("STATUS", matches.groupdict()['cmd'])
        self.assertEqual("foobar", matches.groupdict()['content'])

    def test_status(self):
        """Test status stanza, and nonblocking recv"""
        id = str(uuid.uuid1())
        self.sender.send(f"STATUS[{id}]")
        for i in range(100):
            result = self.sender.recv()
            if result is not None:
                break
            else:
                result = "NO RESULT"
            time.sleep(0.01)

    def test_load(self):
        id = str(uuid.uuid1())
        gcode = "G28 X Y\nG0 X130 Y130\n"
        cmd = f"LOAD[{id}]:{gcode}"
        self.sender.send(cmd)
        result = PlotWorker.parse_result(self.sender.recv(blocking=True))
        self.assertDictEqual(
            {'status': 'OK',
             'id': id,
             'content': '{"size": 21}'},
            result)

    def test_load_and_start(self):
        id = str(uuid.uuid1())
        gcode = "G28 X Y\nG0 X130 Y130\n"
        cmd = f"LOAD[{id}]:{gcode}"
        self.sender.send(cmd)
        result = PlotWorker.parse_result(self.sender.recv(blocking=True))
        self.assertDictEqual(
            {'status': 'OK',
             'id': id,
             'content': '{"size": 21}'},
            result)

        id = str(uuid.uuid1())
        cmd = f"START[{id}]"
        self.sender.send(cmd)
        result = PlotWorker.parse_result(self.sender.recv(blocking=True))

if __name__ == '__main__':
    unittest.main()
