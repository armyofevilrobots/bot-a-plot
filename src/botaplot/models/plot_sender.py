from enum import Enum, auto
import logging
import threading
import json
from io import StringIO
from queue import Queue, Empty
import time
import re
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from botaplot.models.machine import Machine
from botaplot.protocols import PlotJobCancelled

logger = logging.getLogger(__name__)

#
# class PlotThread(QThread):
#     """
#     Runs a counter thread.
#     """
#     countChanged = pyqtSignal(int, int, str)
#
#     def run(self):
#         count = 0
#         while count < TIME_LIMIT:
#             count +=1
#             time.sleep(1)
#             self.countChanged.emit(count)

class PlotWorkerState(Enum):
    READY = auto()
    PAUSED = auto()
    BUSY = auto()
    DYING = auto()
    DEAD = auto()

class InvalidCommandState(ValueError):
    """Used when the state of the plotter is invalid for a command"""
    pass


class PlotWorker(object):
    """
    PlotWorker lives in a separate thread/process/etc... and accepts commands.
    Commands are structured as a command name, then a command ID which is
    surrounded by square braces, then a colon, then the content of
    the command. If no content is required, then no colon is required either.
    The command id should be a unique string, such as a UUIDstr. These are
    not stored indefinitely, and are only used to return "OK[cmd_id]",
    ERROR[cmd_id], or FATAL[cmd_id] messages back to the controller queue.
    All commands must be terminated with \n.
    Protocol is as follows:
    {"COMMAND_NAME": ...data...}
    where...
    LOAD[CMD_ID]: GCODE|HPGL as string ie: {"LOAD": "G28 X Y\nG92\nG0 X123 Y321\n"}
        Where we load a new program that we're going to plot. Will fail if
        the machine is currently plotting
    START[CMD_ID]
        Starts plotting, either at the beginning, or wherever we last PAUSEd.
    CANCEL[CMD_ID]
        Stops plotting and resets command pointer to the beginning.
        NOTE: In this case, the CMD_ID should match the job that is being
        cancelled. That command will return an ERROR[CMD_ID]
    CMD[CMD_ID]
        Send a set of direct commands, either gcode or hp/gl. Should be encapsulated
        as a list of JSON array entries to escape newlines, ie:
        LOAD[123-456-etc..]: ["G28 X Y\n", "G92\n", "M281 S5\n"]
    PAUSE[CMD_ID]
        Pause the plot and retain position
    MOVE[CMD_ID]:(!)X,(!)Y(,Z)
        Move to a specific position. If prefixed with an exclamation mark, the
        position will be interpreted as absolute, otherwise it is moved a
        relative amount. Always in mm. Z is optional, X,Y are mandatory
    PENUP[CMD_ID]
        Lift the pen completely off the paper
    PENDOWN[CMD_ID](:depth)
        Put the pen down. If depth is passed, then a plotter specific depth
        value will be used. This might be either a Z depth, or an M280 PWM
        value for a servo driven pen.
    HOME[CMD_ID]
        Move to the HOME position. Not the origin, this is the real machine home
    ORIGIN[CMD_ID]
        Set origin (absolute X0 Y0) to be the current position.
    STATE[CMD_ID]
        No-op. Used for testing. Always returns some state info in it's OK

    When a command is run, it can return one of the following states:
    OK[cmd_id]: { ...json_encoded_result ... }  # Command OK!
    ERR[cmd_id]: { ...json_encoded_result ... } # Command failed
    FATAL[cmd_id]: { ...json_encoded_result ... } # Fatal. Unrecoverable.

    When an OK or ERR is received, the Worker will try to continue on with
    the next command. If a FATAL is returned, then the worker is in an
    unrecoverable state, and will stop running. It should be destroyed
    and replaced if the user wants to continue on.

    In addition, when a plot is ongoing, another message can be returned:
    PROGRESS[cmd_id]: {"done": cmd_count, "total": cmds_total, "last": last command}
    which will be triggered via callbacks internally, and reflects progress of the
    current plot job.
    """

    cmd_match = re.compile(
        r"^(?P<cmd>[A-Z]*)\[(?P<id>[a-zA-Z0-9\-]*)\]((:)(?P<content>.*))?",
        re.MULTILINE | re.DOTALL)
    result_match = re.compile(
        r"^(?P<status>[A-Z]*)\[(?P<id>[a-zA-Z0-9\-]*)\]((:)(?P<content>.*))?",
        re.MULTILINE | re.DOTALL)

    def __init__(self, machine:Machine, inq:Queue, outq:Queue, die:threading.Event):
        self.machine = machine
        self.inq = inq
        self.outq = outq
        self._die = die
        self.cmd_lock: threading.Lock = threading.Lock()
        self.state_lock: threading.Lock = threading.Lock()
        self._thread = None
        self._program = None  # Will be the posted program later
        self._state = PlotWorkerState.READY
        self.progress_notify = threading.Condition()
        self.progress_q = Queue()
        self.cancel_job = False

    @classmethod
    def new(cls, machine):
        inq = Queue()
        outq = Queue()
        die = threading.Event()
        instance = cls(machine, inq, outq, die)
        thread = threading.Thread(target=instance.run)
        thread.daemon = True
        thread.start()
        while instance.dead is None:
            time.sleep(0.01)
        return instance

    @property
    def state(self):
        with self.state_lock:
            return self._state

    @state.setter
    def set_state(self, new_state: PlotWorkerState):
        with self.state_lock:
            if not isinstance(new_state, PlotWorkerState):
                raise ValueError("Invalid state '%s'" % new_state)
            self._state = new_state

    def state_wrap(self):
        parent = self
        class StateContextWrapper(object):
            def __enter__(self):
                # print("Entering context")
                # locked = parent.state_lock.acquire()
                if parent.state != PlotWorkerState.READY:
                    raise InvalidCommandState(
                        "Plot state %s is invalid for command" %
                        parent.state)
                self.old_state = parent.state
                parent._state = PlotWorkerState.BUSY
                logger.info("Locked!")
                return None

            def __exit__(self, type, value, traceback):
                # print("Exiting context.")
                parent._state = self.old_state
                #parent.state_lock.release()

        return StateContextWrapper()


    def kill(self):
        logger.info(f"{self} Dying.")
        self._die.set()
        return self._die.is_set()

    @property
    def dead(self):
        if not hasattr(self, "_thread"):
            return None  # Special case race
        if self._thread is None:
            return True
        else:
            return False

    def send(self, cmd):
        """Helper function for sending a command to the worker"""
        # print("Sending: %s" % cmd)
        if not self.cmd_match.match(cmd):
            # print("Invalid command")
            raise ValueError(f"Invalid cmd '{cmd[:40]}'")
        with self.cmd_lock:
            self.inq.put(cmd)

    def recv(self, blocking=False):
        """Helper function to retrieve a response from the worker"""
        with self.cmd_lock:
            if not blocking:
                try:
                    return self.outq.get(False)
                except Empty:
                    return None
            else:
                return self.outq.get(True)

    @classmethod
    def parse_result(cls, result):
        try:
            return cls.result_match.match(result).groupdict()
        except Exception as exc:
            return dict(status="ERR", id=None, content={'error': str(exc)})

    def _result(self, kind, id, content=None):
        if isinstance(content, dict):
            content_out = f":{json.dumps(content)}"
        elif content:
            content_out = f":{content}"
        else:
            content_out = ""
        return f"{kind}[{id}]{content_out}"

    def handle_cmd(self, cmd, reentrant=False):
        cmds = json.loads(cmd['content'])
        for line in cmds:
            logger.info(f"Sending single command {line}")
            # print(f"Sending single command {line}")
            self.machine.protocol.single(line, self.machine.transport)
            logger.info("Sent.")
        return self._result("OK", cmd['id'],
                            dict(count=len(cmds)))

    def handle_load(self, cmd, reentrant=False):
        # print("Outside state wrap")
        with self.state_wrap():
            # print("Inside state wrap")
            if reentrant:
                return self._result(
                    "ERR",
                    cmd['id'],
                    dict(error="Existing program already running"))
            assert cmd['cmd'].lower() == "load"
            self._program = cmd['content']
            logger.info("Loading content: %d chars" % len(cmd['content']))
            return self._result("OK", cmd['id'],
                                dict(size=len(self._program)))

    def handle_status(self, cmd, reentrant=False):
        with self.state_wrap():
            assert cmd['cmd'].lower() == "status"
            return self._result("OK", cmd['id'],
                                dict(alive=not self.dead,
                                     thread=self._thread
                                     ))

    def handle_start(self, cmd, reentrant=False):
        with self.state_wrap():
            if reentrant:
                return self._result(
                    "ERR",
                    cmd['id'],
                    dict(error="Existing program already running"))
            try:
                self.machine.plot(self._program, self._progress)
            except PlotJobCancelled:
                return self._result("ERR", cmd['id'],
                                    dict(error="Job cancelled."))
            return self._result("OK", cmd['id'])

    def handle_cancel(self, cmd, reentrant=False):
        # This one is weird. It _has_ to be reentrant
        logger.info("Cancelling job.")
        # print("Cancelling job")
        with self.state_wrap():
            # print("In cancel state wrap")
            logger.info("Cancelling job (IN STATE WRAP).")
            if not reentrant:
                # print("NOT REENTER ON CANCEL")
                return self._result(
                    "ERR",
                    cmd['id'],
                    dict(error="Not currently plotting"))
            if not self.machine.protocol.paused:
                # print("NOT PAUSED NOT CANCELLING")
                return self._result(
                    "ERR",
                    cmd['id'],
                    dict(error="Must pause before cancelling."))
            # print("Setting to cancel!")
            self.cancel_job = True
            return self._result("OK", cmd['id'])


    def _handle(self, cmd_line, reentrant=False):
        cmd = self.cmd_match.match(cmd_line).groupdict()
        method_name = "handle_%s" % cmd['cmd'].lower()
        if hasattr(self, method_name):
            logger.info("Calling method %s with content %s",
                        method_name, cmd['content'])
            try:
                return getattr(self, method_name)(cmd)
            except Exception as exc:
                return self._result("ERR", cmd['id'], dict(error=str(exc)))

    def _progress(self, line_no, total_lines, cmd):
        # Handle a progress callback from the machine/protocol
        self._tick(True)

        if self.cancel_job:
            # print("Actually cancelling")
            self.cancel_job = False
            self.progress_q.put([line_no, total_lines, "JOB CANCELLED"])
            # print("Raising")
            raise PlotJobCancelled("Cancelling plot job")

        # logger.info(f"Line {line_no+1}/{total_lines}: {cmd}")
        self.progress_q.put([line_no, total_lines, cmd])
        # logger.info("Done putting")
        # logger.info("PROGRESS QUEUE: %s", self.progress_q)
        # with self.progress_notify:
        #     self.progress_notify.notifyAll()

        # print(f"Line {line_no+1}/{total_lines}: {cmd}")

    def _tick(self, reentrant=False):
        if not self.inq.empty():
            self.outq.put(self._handle(self.inq.get(), reentrant=reentrant))
            return True

    def run(self):
        """Run the event loop"""
        self._thread = threading.get_ident()
        while not self._die.is_set():
            self._tick()
            time.sleep(0.1)
        self._thread = None





class PlotSender(QObject):
    """slices and sends the plottables"""

    done = pyqtSignal()

    def __init__(self):
        self.runner = None

    def plot(self, plottables=list(), callback=None):
        from .project_model import ProjectModel  # Runtime import because of circular dependency.
        """Create the stuff we'll actually send"""
        ofp = StringIO()
        # plottable = LayerModel.current.plottables["all"][0]
        plottable = plottables[0]
        plottable = plottable.transform(*ProjectModel.current.get_transform(plottable))
        ProjectModel.current.machine.post.write_lines_to_fp(
            plottable, ofp)
        self.gcode = ofp.getvalue()
        logger.debug("GCode is %s", len(self.gcode))
        logger.debug("Callback is %s", callback)
        # TODO: Switch to https://riptutorial.com/pyqt5/example/29500/basic-pyqt-progress-bar
        # TODO: See the PlotThread class I've started above.
        self.kill_plot = threading.Event()
        self.runner = threading.Thread(target=self.plot_monitor, args=[callback, self.kill_plot], daemon=True)
        self.runner.start()
        return True

    def pause(self, paused=True):
        from .project_model import ProjectModel  # Runtime import because of circular dependency.
        ProjectModel.current.machine.protocol.paused = paused

    def plot_monitor(self, callback):
        from .project_model import ProjectModel  # Runtime import because of circular dependency.
        """Background thread that watches stuff and sends plot commands"""
        sem = threading.Semaphore()

        def _safe_callback(*args, **kw):
            logger.debug("Callback: %s", args)
            with sem:
                callback(*args, **kw)

        logger.debug("The LM machine callback is %s", callback)
        ProjectModel.current.machine.plot(self.gcode, callback)
