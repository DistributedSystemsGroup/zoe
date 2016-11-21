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
        self.services = {}
        self.name = 'unk'

    def dump(self):
        print('<------- state at time {} -------->'.format(humanfriendly.format_timespan(self.timestamp)))
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

    def eq(self, other):
        return self.scheduler.eq(other.scheduler) and self.platform.eq(other.platform) and self.jobs == other.jobs and self.services == other.services


class SchedulerState:
    def __init__(self):
        self.queue = []

    def dump(self):
        print('Queue: {}'.format(self.queue))

    def eq(self, other):
        return self.queue == other.queue


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

    def eq(self, other):
        return self.nodes == other.nodes


class Service:
    def __init__(self, id):
        self.id = id
        self.status = 'created'

    def __eq__(self, other):
        if isinstance(other, Service):
            return self.id == other.id
        else:
            raise NotImplementedError

    def __str__(self):
        return str(self.id)

state_sequence = []


def queue_dump_special_cb(previous_state, timestamp, event_list):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.name = 'queue_dump'
    state.scheduler.queue = []
    for event in event_list:
        event_match = re.search(r'^exec (?P<exec_id>[0-9]+) \((?P<exec_name>[a-zA-Z0-9\-]+)\) \| essential (?P<essential_list>[0-9,]+) \| elastic (?P<elastic_list>[0-9,]*) \| size hint (?P<size_hint>[0-9]+) \| size (?P<size>[0-9]+)', event)
        if event_match is None:
            print(event)
        exec_id = int(event_match.group('exec_id'))

        essential_services = []
        for id in event_match.group('essential_list').split(','):
            id = int(id)
            if id not in state.services:
                service = Service(id)
                state.services[id] = service
                essential_services.append(service)

        elastic_services = []
        for id in event_match.group('elastic_list').split(','):
            if len(id) == 0:
                continue
            id = int(id)
            if id not in state.services:
                service = Service(id)
                state.services[id] = service
                elastic_services.append(service)

        if exec_id not in state.jobs:
            state.jobs[exec_id] = {
                'essential': essential_services,
                'elastic': elastic_services
            }
        if exec_id in state.scheduler.queue:
            state.scheduler.queue.remove(exec_id)
        state.scheduler.queue.append(exec_id)
    return state


def platform_status_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.name = 'platform_status'

    for i in range(1, 20, 2):
        node = event_match.group(i)
        mem = event_match.group(i+1)
        state.platform.nodes[node]['free_memory'] = int(mem)
    return state


def service_started_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.name = 'service_started'

    service_id = int(event_match.group('service_id'))
    if service_id in state.services:
        state.services[service_id].status = 'running'
    else:
        print('Service {} started, but is unknown'.format(event_match.group('service_id')))
        assert False
    return state


def service_dead_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.name = 'service_dead'

    service_id = int(event_match.group('service_id'))
    if service_id in state.services:
        state.services[service_id].status = 'dead'
    else:
        print('Service {} died, but is unknown'.format(event_match.group('service_id')))
        assert False
    return state


def service_oom_dead_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.name = 'service_dead_oom'

    service_id = int(event_match.group('service_id'))
    if service_id in state.services:
        state.services[service_id].status = 'oom'
    else:
        print('Service {} died, but is unknown'.format(event_match.group('service_id')))
        assert False
    return state


def service_destroyed_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.name = 'service_destroyed'

    service_id = int(event_match.group('service_id'))
    if service_id in state.services:
        state.services[service_id].status = 'destroyed'
    else:
        print('Service {} was destroyed, but is unknown'.format(event_match.group('service_id')))
        assert False

    for node_name, node in state.platform.nodes.items():
        service = state.services[service_id]
        if service in node['services']:
            node['services'].remove(service)
            break

    return state


def exec_terminated_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.name = 'service_destroyed'
    exec_id = int(event_match.group('exec_id'))

    del state.jobs[exec_id]
    return state


def all_services_started_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.name = 'all_services_started'
    exec_id = int(event_match.group('exec_id'))
    state.scheduler.queue.remove(exec_id)
    return state


def allocation_cb(previous_state, timestamp, event_match):
    state = deepcopy(previous_state)
    state.timestamp = timestamp
    state.name = 'allocation'
    alloc = ast.literal_eval(event_match.group('alloc_dict'))
    for k, v in alloc.items():
        service = state.services[k]
        state.platform.nodes[v]['services'].append(service)
    return state

IGNORE_REGEXES = [
    re.compile(r'Initializing DB manager'),
    re.compile(r'Initializing scheduler'),
    re.compile(r'Connecting to Swarm at'),
    re.compile(r'(Monitor|Checker) thread started'),
    re.compile(r'Starting ZMQ API server...'),
    re.compile(r'Autorestart disabled for service [0-9]+'),
    re.compile(r'api latency:'),
    re.compile(r'Scheduler inner loop, jobs to attempt scheduling'),
    re.compile(r'service [0-9]+, status updated to created$'),
    re.compile(r'starting essential services for execution [0-9]+'),
    re.compile(r'starting elastic service [0-9]+ for execution [0-9]+'),
    re.compile(r'empty queue, exiting inner loop'),
    re.compile(r'No executions could be started, exiting inner loop'),
    re.compile(r'starting elastic service [0-9]+ for execution [0-9]+'),
    re.compile(r'^Service .* terminated$'),
    re.compile(r'Thread termination_[0-9]+ join failed'),
    re.compile(r'-> exec '),
    re.compile(r'^container startup time:'),
    re.compile(r'^service [0-9]+ startup time:'),
    re.compile(r'^Service [0-9]+ got killed by an OOM condition'),
    re.compile(r'Scheduler loop has been triggered'),
    re.compile(r'Allocation after simulation: \{\}'),
    re.compile(r'Docker closed event connection, retrying...')
]

EVENTS_REGEXES = [
    (re.compile(r'SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) # SN (bf[0-9]{2}) \| f ([0-9]+) #'), platform_status_cb),
    (re.compile(r'service (?P<service_id>[0-9]+), status updated to started$'), service_started_cb),
    (re.compile(r'service (?P<service_id>[0-9]+), status updated to dead'), service_dead_cb),
    (re.compile(r'service (?P<service_id>[0-9]+), status updated to oom-killed'), service_oom_dead_cb),
    (re.compile(r'service (?P<service_id>[0-9]+), status updated to destroyed'), service_destroyed_cb),
    (re.compile(r'Execution (?P<exec_id>[0-9]+) terminated successfully'), exec_terminated_cb),
    (re.compile(r'execution (?P<exec_id>[0-9]+): all services started'), all_services_started_cb),
    (re.compile(r'Allocation after simulation: (?P<alloc_dict>{[0-9: \',bf]+})'), allocation_cb)
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
    #fp = open('/home/ubuntu/zoe-papers/experiments/results/run_8_master_log', 'r')
    fp = open('/tmp/master.log', 'r')
    initial_timestamp = None
    accumulate_log_lines = False
    accumulator = []

    for line in fp:
        m = re.match(LOG_LINE_REGEX, line)
        if m is None:
            continue

        timestamp = datetime.strptime(m.group('timestamp'), '%Y-%m-%d %H:%M:%S,%f')
        if initial_timestamp is None:
            initial_timestamp = timestamp
        timestamp = (timestamp - initial_timestamp).total_seconds()

        found = False
        for regex in IGNORE_REGEXES:
            if regex.match(m.group('event')) is not None:
                found = True
                break
        if found:
            continue

        if len(state_sequence) == 0:
            state_sequence.append(State(timestamp))

        found = False
        for regex, event_cb in EVENTS_REGEXES:
            ev_match = regex.match(m.group('event'))
            if ev_match is not None:
                new_state = event_cb(state_sequence[-1], timestamp, ev_match)
                state_sequence.append(new_state)
                found = True
                break
        if found:
            continue

        if re.search(r'End dump', line):
            accumulate_log_lines = False
            new_state = queue_dump_special_cb(state_sequence[-1], timestamp, accumulator)
            state_sequence.append(new_state)
            continue
        if accumulate_log_lines:
            accumulator.append(m.group('event'))
            continue

        if re.search(r'Queue dump after sorting', line):
            accumulate_log_lines = True
            accumulator = []
            continue

        if not found:
            print('Event {} is not known'.format(m.group('event')))

    return state_sequence


def _draw_node(stdscr, node_name, node, y, x):
    stdscr.addstr(y, x, node_name + ' {}'.format(humanfriendly.format_size(node['free_memory'])))

    y += 1
    for service in node['services']:
        stdscr.addstr(y, x, str(service))
        y += 1


def _draw_platform(stdscr, pl_state, y):
    stdscr.addstr(y, 0, 'Node details:')
    y += 1
    x = 0
    node_width = 15
    for node_name, node in sorted(pl_state.nodes.items()):
        _draw_node(stdscr, node_name, node, y, x)
        x += node_width + 1


def _draw_state(stdscr, index, state_sequence):
    stdscr.clear()
    ESSENTIAL_COLOR = curses.color_pair(1)
    ELASTIC_COLOR = curses.color_pair(3)
    EXEC_ID_COLOR = curses.color_pair(2)

    state = state_sequence[index]
    stdscr.addstr(0, 0, '--------- state {} ({}) @ time {}------------'.format(state.name, index, humanfriendly.format_timespan(state.timestamp)))

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
        for service in v['essential']:
            id = str(service)
            if service.status == 'running':
                stdscr.addstr(y, x, id, ESSENTIAL_COLOR | curses.A_BOLD)
            elif service.status == 'oom':
                stdscr.addstr(y, x, id, ESSENTIAL_COLOR | curses.A_UNDERLINE)
            else:
                stdscr.addstr(y, x, id, ESSENTIAL_COLOR)
            x += len(id) + 1
        for service in v['elastic']:
            id = str(service)
            if service.status == 'running':
                stdscr.addstr(y, x, id, ELASTIC_COLOR | curses.A_BOLD)
            elif service.status == 'oom':
                stdscr.addstr(y, x, id, ELASTIC_COLOR | curses.A_UNDERLINE)
            else:
                stdscr.addstr(y, x, id, ELASTIC_COLOR)
            x += len(id) + 1
        y += 1

    stdscr.addstr(y, 0, 'Scheduler sorted queue: head->{}'.format(state.scheduler.queue))
    y += 1
    _draw_platform(stdscr, state.platform, y)


def ui(stdscr, state_sequence):
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
    current_state = 0
    _draw_state(stdscr, current_state, state_sequence)

    while True:
        stdscr.refresh()
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


def clean_states(states):
    print('Cleaning up states where nothing changes')
    print('Before: {} states'.format(len(states)))
    states_count = len(states)
    i = 0
    while i < states_count:
        if i + 1 >= len(states):
            break
        if states[i].eq(states[i + 1]):
            del states[i + 1]
            states_count -= 1
        else:
            i += 1
    print('After: {} states'.format(len(states)))

if __name__ == "__main__":
    states = main()
    clean_states(states)
    curses.wrapper(ui, states)
