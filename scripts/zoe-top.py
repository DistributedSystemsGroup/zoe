#!/usr/bin/python3

import curses
import os

from zoe_lib.statistics import ZoeStatisticsAPI
from zoe_lib.executions import ZoeExecutionsAPI
from zoe_lib.services import ZoeServiceAPI

class State:
    def __init__(self):
        self.scheduler = SchedulerState()
        self.platform = PlatformState()
        self.jobs = {}
        self.services = {}
        self.name = 'unk'


class SchedulerState:
    def __init__(self):
        self.queue = []


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


def get_state_from_zoe():
    state = State()

    zoe_url = os.environ['ZOE_URL']
    zoe_user = os.environ['ZOE_USER']
    zoe_pass = os.environ['ZOE_PASS']

    # Executions
    exec_api = ZoeExecutionsAPI(zoe_url, zoe_user, zoe_pass)
    services_api = ZoeServiceAPI(zoe_url, zoe_user, zoe_pass)

    execs = exec_api.list()
    for e_id, e in execs.items():
        if e['status'] != 'running' and e['status'] != 'scheduled' and e['status'] != 'starting':
            continue
        essential_list = []
        for s_id in e['services']:
            s = services_api.get(s_id)
            s_o = Service(s_id)
            if s['docker_status'] == 'started':
                s_o.status = 'running'
            elif s['docker_status'] == 'oom-killed':
                s_o.status = 'oom'
            else:
                s_o.status = 'dead'
            essential_list.append(s_o)
            state.services[s_id] = s_o

        state.jobs[e_id] = {
            'name': e['name'],
            'essential': essential_list,
            'elastic': []
        }

    return state


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


def _draw_node(stdscr, node_name, node, y, x):
    stdscr.addstr(y, x, node_name)

    y += 1
    for service in node['services']:
        stdscr.addstr(y, x, str(service))
        y += 1


def _draw_platform(stdscr, pl_state, y):
    stdscr.addstr(y, 0, 'Node details:')
    y += 1
    x = 0
    node_width = 5
    for node_name, node in sorted(pl_state.nodes.items()):
        _draw_node(stdscr, node_name, node, y, x)
        x += node_width + 1


def _draw_state(stdscr, state):
    ESSENTIAL_COLOR = curses.color_pair(1)
    ELASTIC_COLOR = curses.color_pair(3)
    EXEC_ID_COLOR = curses.color_pair(2)

    stdscr.clear()

    stdscr.addstr(0, 0, '- -------- state {} ------------'.format(state.name))

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
        s = '  {} ({})'.format(v['name'], k)
        stdscr.addstr(y, x, s, EXEC_ID_COLOR)
        x += len(s) + 1
        s = ':'
        stdscr.addstr(y, x, s)
        x += len(s) + 1
        for service in v['essential']:
            s_id = str(service)
            if service.status == 'running':
                stdscr.addstr(y, x, s_id, ESSENTIAL_COLOR | curses.A_BOLD)
            elif service.status == 'oom':
                stdscr.addstr(y, x, s_id, ESSENTIAL_COLOR | curses.A_UNDERLINE)
            else:
                stdscr.addstr(y, x, s_id, ESSENTIAL_COLOR)
            x += len(s_id) + 1
        for service in v['elastic']:
            s_id = str(service)
            if service.status == 'running':
                stdscr.addstr(y, x, s_id, ELASTIC_COLOR | curses.A_BOLD)
            elif service.status == 'oom':
                stdscr.addstr(y, x, s_id, ELASTIC_COLOR | curses.A_UNDERLINE)
            else:
                stdscr.addstr(y, x, s_id, ELASTIC_COLOR)
            x += len(s_id) + 1
        y += 1

    stdscr.addstr(y, 0, 'Scheduler sorted queue: head->{}'.format(state.scheduler.queue))
    y += 1
    _draw_platform(stdscr, state.platform, y)


def ui(stdscr):
    curses.halfdelay(10)

    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)

    current_state = get_state_from_zoe()

    _draw_state(stdscr, current_state)

    while True:
        stdscr.refresh()
        c = stdscr.getch()
        if c == ord('q'):
            break

        stdscr.addstr(0, 0, '+')
        stdscr.refresh()
        current_state = get_state_from_zoe()
        stdscr.addstr(0, 0, '-')
        stdscr.refresh()
        _draw_state(stdscr, current_state)


if __name__ == "__main__":
    curses.wrapper(ui)
