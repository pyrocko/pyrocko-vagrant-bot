#!/usr/bin/env python3

from pyrocko_vagrant_bot.commander import VagrantCommander
from pyrocko_vagrant_bot.server import MattermostCommand, MattermostResponse

commander = VagrantCommander('/home/marius/Development/pyrocko')

payload = '&'.join(
    ['channel_id=cniah6qa73bjjjan6mzn11f4ie',
     'channel_name=Housekeeping',
     'command=/vagrant',
     'response_url=not+supported+yet',
     'team_domain=someteam',
     'team_id=rdc9bgriktyx9p4kowh3dmgqyc',
     'text=%s',
     'token=xr3j5x3p4pfk7kk6ck7b4e6ghh',
     'user_id=c3a4cqe3dfy6dgopqt8ai3hydh',
     'user_name=somename'])


def test_commands():
    for cmd in ['help', 'list', 'log', 'run ubuntu-14.4', 'inspect']:
        resp = MattermostResponse()
        MC = MattermostCommand((payload % cmd).encode('ascii'))
        commander(MC, resp)
        print('\nCommand %s\n---------------------' % cmd)
        print(resp.text)


if __name__ == '__main__':
    test_commands()
