#!/usr/bin/env python3
import re
import os
import glob
import os.path as op
import logging

import threading
import subprocess


logger = logging.getLogger('VagrantCommander')


class VagrantMachine(object):

    class ExecuteVM(threading.Thread):

        def __init__(self, name, executeable):
            self.name = name
            self.executeable = executeable

        def run(self):
            subprocess.call([self.executeable])

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

    def results(self):
        rstr = ''
        outfiles = glob.glob(op.join(self.path, 'test-*.py[23].out'))
        for fn in outfiles:
            rstr += self.parse_result(fn)
        if not outfiles:
            rstr += '*No log available*'
        return rstr

    @staticmethod
    def parse_result(fn, show_skips=False):
        with open(fn, 'r') as f:
            m = re.search(r'/test-(.*)\.py([23])\.out$', fn)
            branch = m.group(1)
            py_version = m.group(2)
            print('   python: %s' % py_version)

            print('      log: %s' % fn)
            print('      branch: %s' % branch)

            txt = f.read()

            m = re.search(r'---+\nTOTAL +(.+)\n---+', txt)
            if m:
                print('      coverage: %s' % m.group(1))

            m = re.search(r'^((OK|FAILED)( +\([^\)]+\))?)', txt, re.M)
            if m:
                print('      tests: %s' % m.group(1))

            if show_skips:
                count = {}
                for x in re.findall(r'... SKIP: (.*)$', txt, re.M):
                    if x not in count:
                        count[x] = 1
                    else:
                        count[x] += 1

                for x in sorted(count.keys()):
                    print('         skip: %s (%ix)' % (x, count[x]))

            for x in re.findall(r'^ERROR: .*$', txt, re.M):
                print('         %s' % x)

            for x in re.findall(r'^FAIL: .*$', txt, re.M):
                print('         %s' % x)

    def status(self, path):
        pass

    def run(self, path):
        self.thread.start()

    def stop(self):
        self.thread.join()

    @property
    def is_running(self):
        return self.thread.isAlive()

    @property
    def quoted_name(self):
        return '`%s`' % self.name


class VagrantCommander(object):
    handlers = {}

    def __init__(self, path):
        self.path = path
        self.response = ''

        self.machines = []
        self.scan_machines()

    @staticmethod
    def register_command(cls, command):
        def register(func):
            VagrantCommander.handlers[command] = func
            return func
        return register

    def __call__(self, event):

        for re_cmd, hdl in self.handlers.items():
            match = re.compile(r'%s' % re_cmd)
            if match.findall(event.text):
                self.response = hdl(self)
                return
        self.response = 'Unknown command _%s_' % event.text

    @register_command('commands|help')
    def show_help(self):
        return '''Vagrant Bot commands:
* `list|machines` Lists all available deployment machines
* `run <all|vm_name> Start a deployment on all or special VM
* `status` Show status of running deployments'''

    @register_command('status')
    def show_status(self):
        return

    @register_command('list|machines')
    def show_machines(self):
        rstr = 'Available Machines:'
        if not self.machines:
            rstr += '\n*Could not get machines*'
        else:
            rstr += '\n* ' + \
                '\n* '.join([m.quoted_name for m in self.machines])
        return rstr

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
                logger.warning(e.message)
                break
            logger.info('Added machine %s (%s)' % (machine.name, machine.path))

    def get_response(self):
        return self.response
