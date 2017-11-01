#!/usr/bin/env python3
import re
import io
import os
import glob
import os.path as op
import logging

import threading
import subprocess

logger = logging.getLogger('VagrantCommander')
HANDLERS = {}


class VagrantMachine(object):

    class ExecuteVM(threading.Thread):

        def __init__(self, name, executeable):
            threading.Thread.__init__(self)
            self.name = name
            self.executeable = executeable
            self.path = op.dirname(executeable)
            self.process = None

            self.stdout = io.StringIO()
            self.stderr = io.StringIO()

        def run(self):
            self.process = subprocess.Popen(
                [self.executeable],
                cwd=self.path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            self.stdout.write(self.process.stdout.read())
            self.stderr.write(self.process.stderr.read())

        def isfinished(self):
            if self.process is None:
                return False
            return self.process.poll() or False

    def __init__(self, path):
        self.verify_path(path)

        self.path = path
        self.name = op.basename(path)
        self.thread = self.ExecuteVM(
            self.name, op.join(self.path, 'outside.sh'))

    @staticmethod
    def verify_path(path):
        files = os.listdir(path)
        if not 'inside.sh' and 'outside.sh' in files:
            raise AttributeError('Not a pyrocko Vagrant folder %s' % path)
        return True

    def get_log(self):
        rstr = '```\n'
        outfiles = glob.glob(op.join(self.path, 'test-*.py[23].out'))
        if not outfiles:
            return '*No log available*'
        for fn in outfiles:
            rstr += self.parse_result(fn)
        rstr += '```\n'
        return rstr

    @staticmethod
    def parse_result(fn, show_skips=False):
        rstr = ''
        with open(fn, 'r') as f:
            m = re.search(r'/test-(.*)\.py([23])\.out$', fn)
            branch = m.group(1)
            py_version = m.group(2)
            rstr += '   python: %s\n' % py_version
            rstr += '   branch: %s\n' % branch

            txt = f.read()

            m = re.search(r'---+\nTOTAL +(.+)\n---+', txt)
            if m:
                rstr += '      coverage: %s\n' % m.group(1)

            m = re.search(r'^((OK|FAILED)( +\([^\)]+\))?)', txt, re.M)
            if m:
                rstr += '      tests: %s\n' % m.group(1)

            if show_skips:
                count = {}
                for x in re.findall(r'... SKIP: (.*)$', txt, re.M):
                    if x not in count:
                        count[x] = 1
                    else:
                        count[x] += 1

                for x in sorted(count.keys()):
                    rstr += '         skip: %s (%ix)\n' % (x, count[x])

            for x in re.findall(r'^ERROR: .*$', txt, re.M):
                rstr += '         %s\n' % x

            for x in re.findall(r'^FAIL: .*$', txt, re.M):
                rstr += '         %s\n' % x
        return rstr

    def status(self, path):
        pass

    def run(self):
        logger.info('Starting Vagrant machine %s...' % self.name)
        self.thread.start()

    def stop(self):
        self.thread.join()

    @property
    def is_running(self):
        return self.thread.isAlive()

    @property
    def status_str(self):
        return ':running_man: running' if self.is_running else 'stopped'

    @property
    def name_quoted(self):
        return '`%s`' % self.name


def register_command(command):
    def register(func):
        HANDLERS[command] = func
        return func
    return register


class VagrantCommander(object):
    HANDLERS = HANDLERS

    def __init__(self, path):
        self.path = path

        self.machines = []
        self.scan_machines()

    def __call__(self, event, resp):
        for pattern, hdl in self.HANDLERS.items():
            match = re.compile(pattern)
            if match.findall(event.text):
                hdl(self, event, resp)
                return resp
        self.response = 'Unknown command _%s_' % event.text
        return resp

    @register_command(r'commands|help')
    def show_help(self, event, resp):
        ''' Show this help '''
        resp.text = 'Vagrant Bot commands:\n'
        resp.text += '\n'.join(['* `%s` %s' % (ptn, f.__doc__.strip())
                                for ptn, f in HANDLERS.items()])

    @register_command(r'list|machines')
    def show_machines(self, event, resp):
        ''' Lists all available machines and corresponding status '''
        resp.text = 'Available Machines:\n'
        resp.text += '\n'.join(['* %s %s'
                                % (m.name_quoted, m.status_str)
                                for m in self.machines])

    @register_command(r'run|start')
    def run_machine(self, event, resp):
        ''' Start Vagrant machines, space seperated or `all`'''
        for m in self._get_machines_from_text(event.text, resp):
            m.run()
            resp.text += '%s started!\n' % m.name_quoted
        resp.text = resp.text[:-2]

    @register_command(r'inspect')
    def inspect_machine(self, event, resp):
        ''' Inspect machine's stdout and stderr, space seperated or `all` '''
        for m in self._get_machines_from_text(event.text, resp):
            resp.text += 'Inspection of %s\n' % m.name_quoted
            resp.text += '*STDOUT*\n```\n%s\n```\n' % m.stdout.getvalue()
            resp.text += '*STDERR*\n```\n%s\n```\n' % m.stderr.getvalue()

    @register_command(r'log|status')
    def show_log(self, event, resp):
        ''' Show logs for deployments, space seperated or `all` '''
        for m in self._get_machines_from_text(event.text, resp):
            resp.text += 'Showing log for %s:\n' % m.name_quoted
            resp.text += m.get_log()

    def _get_machines_from_text(self, text, resp):
        machines = []
        patterns = [m.lower() for m in text.split()[1:]]
        if not patterns:
            resp.text = 'No machines given!'
        for m in self.machines:
            if m.name.lower() in patterns or 'all' in patterns:
                machines.append(m)

        return machines

    def scan_machines(self):
        path = op.join(self.path, 'maintenance', 'vagrant')
        if not op.exists(path):
            raise OSError('Path %s does not exist!' % path)

        active_machines = [m.path for m in self.machines]
        for mp in os.listdir(path):
            mp = op.join(path, mp)
            if mp in active_machines:
                break
            try:
                machine = VagrantMachine(mp)
                self.machines.append(machine)
            except AttributeError as e:
                logger.warning(e)
                break
            logger.info('Added machine %s (%s)' % (machine.name, machine.path))
