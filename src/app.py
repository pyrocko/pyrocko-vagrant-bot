import os.path as op
import argparse
import logging
from pyrocko import guts

import requests

from .server import WebhookServerConfig

logger = logging.getLogger('vagrant-webhook')


def serve(config_file):
    config = guts.load(filename=config_file)
    server_class = config.get_server()
    vagrant = config.get_handler()

    logger.warning('Starting server on %s:%d'
                   % (server_class.config_address, server_class.config_port))

    httpd = server_class(
        (server_class.config_address, server_class.config_port),
        vagrant)
    httpd.serve_forever()


def init(config_file):
    if op.exists(config_file):
        print('File %s already exists, not overwriting' % config_file)
        return
    config = WebhookServerConfig()
    config.dump(filename=config_file)


def send_request(config_file):
    import time

    wait = 3
    config = guts.load(filename=config_file)
    headers = {
        'Accept': 'application/json'
    }
    payload = '&'.join([
        'channel_id=cniah6qa73bjjjan6mzn11f4ie',
        'channel_name=Housekeeping',
        'command=/vagrant',
        'response_url=not+supported+yet',
        'team_domain=someteam',
        'team_id=rdc9bgriktyx9p4kowh3dmgqyc',
        'text=help',
        'token=xr3j5x3p4pfk7kk6ck7b4e6ghh',
        'user_id=c3a4cqe3dfy6dgopqt8ai3hydh',
        'user_name=somename',
    ])
    print(len(payload))

    session = requests.Session()
    if config.address == '0.0.0.0':
        config.address = '127.0.0.1'
    while True:
        logger.info('Posting to %s:%d...' % (config.address, config.port))
        try:
            r = session.post('http://%s:%d' % (config.address, config.port),
                             data=payload, headers=headers, timeout=1)
            print('Response: %s' % r.json())
        except Exception:
            logger.warning('Not responding, trying again in %d s' % wait)
        time.sleep(wait)


def app():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'action',
        help='Action to take',
        choices=['init', 'serve', 'request'])
    parser.add_argument(
        'file',
        help='Configuration file')

    args = parser.parse_args()

    filename = op.abspath(args.file)
    if args.action == 'init':
        init(filename)

    if args.action == 'serve':
        serve(filename)

    if args.action == 'request':
        send_request(filename)


if __name__ == '__main__':
    app()
