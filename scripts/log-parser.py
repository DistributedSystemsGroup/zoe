#!/usr/bin/python3

import ast
import re
from datetime import datetime
from copy import deepcopy
import curses

import humanfriendly

# 2016-10-13 13:25:28,348 INFO MainThread->main: Initializing DB manager
LOG_LINE_REGEX = r'^(?P<timestamp>[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}) (?P<level>DEBUG|INFO|WARNING|ERROR|TRACE) (?P<component>[^:]+): (?P<event>.*)$'


class State:
    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.scheduler = SchedulerState()
        self.platform = PlatformState()
        self.jobs = {}

    def dump(self):
        print('<------- state at time {0:.3f} -------->'.format(self.timestamp))
        print('Jobs')
        for k, v in sorted(self.jobs.items()):
            essential = " ".join(["{}:{}".format(x, y) for x, y in v['essential']])
            elastic = " ".join(["{}:{}".format(x, y) for x, y in v['elastic']])
            print('  {}: ES {} | EL {}'.format(k, essential, elastic))
        print('Scheduler')
        self.scheduler.dump()
        print('Platform')
        self.platform.dump()
        print('<------- end state --------->')


class SchedulerState:
    def __init__(self):
        self.triggered = False
        self.queue = []

    def dump(self):
        print('Triggered: {}'.format(self.triggered))
        print('Queue: {}'.format(self.queue))


class PlatformState:
    def __init__(self):
        self.nodes = {
            'bf12': {
                'free_memory': -1,
                'services': []
            },
            'bf13': {
                'free_memory': -1,
                'services': []
            },
            'bf14': {
                'free_memory': -1,
                'services': []
            },
            'bf15': {
                'free_memory': -1,
                'services': []
            },
            'bf16': {
                'free_memory': -1,
                'services': []
            },
            'bf17': {
                'free_memory': -1,
                'services': []
            },
            'bf18': {
                'free_memory': -1,
                'services': []
            },
            'bf19': {
                'free_memory': -1,
                'services': []
            },
            'bf20': {
                'free_memory': -1,
                'services': []
            },
            'bf21': {
                'free_memory': -1,
                'services': []
            }
        }

    def dump(self):
        for k, v in sorted(self.nodes.items()):
            print('{}: {} {}'.format(k, humanfriendly.format_size(v['free_memory']), v['services']))

state_sequence = []


def sched_trigger_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.scheduler.triggered = True
    return state


def sched_trigger_empty_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.scheduler.triggered = True
    # state.scheduler.queue = []
    return state


def queue_dump_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.scheduler.triggered = False
    exec_id = int(event_match.group('exec_id'))
    essential_services = [[x, 'S'] for x in event_match.group('essential_list').split(',')]
    elastic_services = [[x, 'S'] for x in event_match.group('elastic_list').split(',') if len(x) > 0]
    if exec_id not in state.jobs:
        state.jobs[exec_id] = {
            'essential': essential_services,
            'elastic': elastic_services
        }
    state.scheduler.queue.append(exec_id)
    return state

def platform_status_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.scheduler.triggered = False

    for i in range(1, 20, 2):
        node = event_match.group(i)
        mem = event_match.group(i+1)
        state.platform.nodes[node]['free_memory'] = int(mem)
    return state


def service_started_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.scheduler.triggered = False

    found = False
    for j in state.jobs.values():
        for s in j['essential']:
            if s[0] == event_match.group('service_id'):
                s[1] = 'R'
                found = True
                break
        if found:
            break
        for s in j['elastic']:
            if s[0] == event_match.group('service_id'):
                s[1] = 'R'
                found = True
                break
    assert found
    return state


def service_dead_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.scheduler.triggered = False

    found = False
    for j in state.jobs.values():
        for s in j['essential']:
            if s[0] == event_match.group('service_id'):
                s[1] = 'D'
                found = True
                break
        if found:
            break
        for s in j['elastic']:
            if s[0] == event_match.group('service_id'):
                s[1] = 'D'
                found = True
                break
    assert found
    return state


def all_services_started_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.scheduler.triggered = False
    exec_id = int(event_match.group('exec_id'))
    state.scheduler.queue.remove(exec_id)
    return state


def allocation_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.scheduler.triggered = False
    alloc = ast.literal_eval(event_match.group('alloc_dict'))
    for k, v in alloc.items():
        state.platform.nodes[v]['services'].append(k)
    return state

IGNORE_REGEXES = [
    r'Initializing DB manager',
    r'Initializing scheduler',
    r'Connecting to Swarm at',
    r'(Monitor|Checker) thread started',
    r'Starting ZMQ API server...',
    r'--> Queue dump after sorting',
    r'--> End dump',
    r'Autorestart disabled for service [0-9]+',
    r'api latency:',
    r'Scheduler inner loop, jobs to attempt scheduling',
    r'^-> exec ',
    r'service [0-9]+, status updated to created$',
    r'service [0-9]+, status updated to destroyed',
    r'starting essential services for execution [0-9]+',
    r'starting elastic service [0-9]+ for execution [0-9]+',
    r'empty queue, exiting inner loop',
    r'starting elastic service [0-9]+ for execution [0-9]+',
    r'^Service .* terminated$',
    r'Thread termination_[0-9]+ join failed'
]

EVENTS_REGEXES = [
    (r'Scheduler loop has been triggered$', sched_trigger_cb),
    (r'Scheduler loop has been triggered, but the queue is empty$', sched_trigger_empty_cb),
    (r'^exec (?P<exec_id>[0-9]+) \((?P<exec_name>[a-zA-Z0-9\-]+)\) \| essential (?P<essential_list>[0-9,]+) \| elastic (?P<elastic_list>[0-9,]*) \| size hint (?P<size_hint>[0-9]+) \| size (?P<size>[0-9]+)', queue_dump_cb),
    (r'SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) #', platform_status_cb),
    (r'service (?P<service_id>[0-9]+), status updated to started$', service_started_cb),
    (r'service (?P<service_id>[0-9]+), status updated to dead', service_dead_cb),
    (r'execution (?P<exec_id>[0-9]+): all services started', all_services_started_cb),
    (r'Allocation after simulation: (?P<alloc_dict>{[0-9: \',bf]+})', allocation_cb)

]


def _init_curses():
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)

    return stdscr


def _end_curses(stdscr):
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()


def main():
    fp = open('master-log.txt', 'r')
    initial_timestamp = None

    for line in fp:
        m = re.match(LOG_LINE_REGEX, line)
        if m is None:
            continue
        timestamp = datetime.strptime(m.group('timestamp'), '%Y-%m-%d %H:%M:%S,%f')

        found = False
        for regex in IGNORE_REGEXES:
            if re.match(regex, m.group('event')) is not None:
                found = True
                break
        if found:
            continue

        if initial_timestamp is None:
            initial_timestamp = timestamp
        timestamp = (timestamp - initial_timestamp).total_seconds()

        if len(state_sequence) == 0:
            state_sequence.append(State(timestamp))

        found = False
        for regex, event_cb in EVENTS_REGEXES:
            ev_match = re.match(regex, m.group('event'))
            if ev_match is not None:
                new_state = event_cb(state_sequence[-1], timestamp, ev_match)
                state_sequence.append(new_state)
                found = True
                break

        if not found:
            print('Event {} is not known'.format(m.group('event')))

    return state_sequence


def _draw_node(stdscr, node_name, node, y, x):
    stdscr.addstr(y, x, node_name)

    y += 1
    for service in node['services']:
        stdscr.addstr(y, x, str(service))
        y += 1


def _draw_platform(stdscr, pl_state, y):
    x = 0
    node_width = 5
    for node_name, node in sorted(pl_state.nodes.items()):
        _draw_node(stdscr, node_name, node, y, x)
        x += node_width + 1


def _draw_state(stdscr, index, state_sequence):
    stdscr.clear()
    ESSENTIAL_COLOR = curses.color_pair(1)
    ELASTIC_COLOR = curses.color_pair(3)
    EXEC_ID_COLOR = curses.color_pair(2)

    state = state_sequence[index]
    stdscr.addstr(0, 0, '--------- state {} @ time {:.3f}------------'.format(index, state.timestamp))

    s = 'Known executions'
    x = 0
    stdscr.addstr(1, x, s)
    x += len(s) + 1
    s = 'essential'
    stdscr.addstr(1, x, s, ESSENTIAL_COLOR)
    x += len(s) + 1
    s = 'elastic'
    stdscr.addstr(1, x, s, ELASTIC_COLOR)
    y = 2
    for k, v in sorted(state.jobs.items()):
        x = 0
        s = '  {}'.format(k)
        stdscr.addstr(y, x, s, EXEC_ID_COLOR)
        x += len(s) + 1
        s = ':'
        stdscr.addstr(y, x, s)
        x += len(s) + 1
        for id, running in v['essential']:
            if running == 'R':
                stdscr.addstr(y, x, id, ESSENTIAL_COLOR | curses.A_BOLD)
            else:
                stdscr.addstr(y, x, id, ESSENTIAL_COLOR)
            x += len(id) + 1
        for id, running in v['elastic']:
            if running == 'R':
                stdscr.addstr(y, x, id, ELASTIC_COLOR | curses.A_BOLD)
            else:
                stdscr.addstr(y, x, id, ELASTIC_COLOR)
            x += len(id) + 1
        y += 1

    y = 8
    stdscr.addstr(y, 0, 'Scheduler state')
    y += 1
    if state.scheduler.triggered:
        stdscr.addstr(y, 0, 'Triggered: [X]')
    else:
        stdscr.addstr(y, 0, 'Triggered: [ ]')

    y += 1
    stdscr.addstr(y, 0, 'Queue: {}'.format(state.scheduler.queue))
    y += 1
    _draw_platform(stdscr, state.platform, y)


def ui(stdscr, state_sequence):
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
    current_state = 0
    _draw_state(stdscr, current_state, state_sequence)

    while True:
        c = stdscr.getch()
        if c == ord('q'):
            break
        elif c == curses.KEY_RIGHT:
            if current_state == len(state_sequence) - 1:
                curses.flash()
            else:
                current_state += 1
        elif c == curses.KEY_LEFT:
            if current_state == 0:
                curses.flash()
            else:
                current_state -= 1
        elif c == curses.KEY_HOME:
            current_state = 0
        elif c == curses.KEY_END:
            current_state = len(state_sequence) - 1

        _draw_state(stdscr, current_state, state_sequence)


if __name__ == "__main__":
    states = main()
    curses.wrapper(ui, states)
