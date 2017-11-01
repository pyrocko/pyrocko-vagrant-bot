#!/usr/bin/env python3\
import json
import os.path as op
import logging
import ssl
import urllib

from pyrocko import guts
from http import server
from .commander import VagrantCommander

logger = logging.getLogger('vagrant-webhook')


class WebhookServerConfig(guts.Object):
    address = guts.String.T(
        help='Server address',
        default='0.0.0.0')
    port = guts.Int.T(
        help='Server Port',
        default=8085)
    ssl_certificate = guts.String.T(
        help='SSL Certificate',
        default='None')
    repository_path = guts.String.T(
        help='Path of the repository',
        default='~/Development/pyrocko')

    def get_server(self):
        server = WebhookServer
        server.config_address = self.address
        server.config_port = self.port
        if self.ssl_certificate == 'None':
            self.ssl_certificate = None
        server.config_certfile = self.ssl_certificate
        return server

    def get_handler(self):
        webhook = VagrantWebhook
        webhook.commander = VagrantCommander(
            path=self.repository_path)
        return VagrantWebhook


class WebhookServer(server.HTTPServer):

    def __init__(self, *args, **kwargs):
        server.HTTPServer.__init__(self, *args, **kwargs)

        if self.config_certfile is not None:
            if not op.exists(self.config_certfile):
                logger.warning('Could not open certificate %s'
                               % self.config_certfile)
                return
            self.socket = ssl.wrap_socket(
                self.socket,
                certfile=self.config_certfile,
                server_side=True)


class VagrantCommand(object):
    def __init__(self, payload):
        for k, v in urllib.parse.parse_qs(payload).items():
            self.__setattr__(k.decode(), v[0].decode())


class VagrantWebhook(server.SimpleHTTPRequestHandler):
    server_version = 'pyrocko-vagrant-webhook/0.1'

    @staticmethod
    def prepare_message(message):
        resp = {
            'response_type': 'in_channel',
            'text': message,
        }
        return str.encode(json.dumps(resp))

    def do_GET(self):
        # self.send_error(501, 'Not Implemented')
        resp = b'Yessir!'
        self.send_response(200, 'OK')
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-length', len(resp))
        self.end_headers()
        self.wfile.write(resp)

    def do_HEAD(self):
        self.send_error(501, 'Not Implemented')

    def do_POST(self):
        content_length = int(self.headers['Content-length'])
        if content_length > 512:
            self.send_response(400, 'Bad Request')
            return

        try:
            command = VagrantCommand(self.rfile.read(content_length))
            self.commander(command)
        except Exception as e:
            print(e)
            self.send_response(400, 'Bad Request')
            return

        self.commander(command)
        resp = self.prepare_message(self.commander.get_response())
        self.send_response(200, 'OK')
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-length', len(resp))
        self.end_headers()

        self.wfile.write(resp)
