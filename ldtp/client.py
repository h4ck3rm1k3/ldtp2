import xmlrpclib
from socket import error as SocketError
from time import sleep
import subprocess
import sys
from client_exception import LdtpExecutionError, ERROR_CODE

class _Method(xmlrpclib._Method):
    def __call__(self, *args, **kwargs):
        args += (kwargs,)
        return self.__send(self.__name, args)

class LdtpClient(xmlrpclib.ServerProxy):
    def __init__(self, uri, encoding=None, verbose=0, use_datetime=0):
        xmlrpclib.ServerProxy.__init__(
            self, uri, Transport(), encoding, verbose, 1, use_datetime)

    def __getattr__(self, name):
        # magic method dispatcher
        return _Method(self._ServerProxy__request, name)

    def kill_daemon(self):
        self._ServerProxy__transport.kill_daemon()
        
class Transport(xmlrpclib.Transport):
    def _spawn_daemon(self):
        self._daemon = subprocess.Popen(
            ['python', '-c', 'import ldtpd; ldtpd.main()'],
            stderr=sys.stderr)
        sleep(2)

    def request(self, host, handler, request_body, verbose=0):
        try:
            return xmlrpclib.Transport.request(
                self, host, handler, request_body, verbose=0)
        except SocketError, e:
            if e.errno == 111 and 'localhost' in host:
                self._spawn_daemon()
                return xmlrpclib.Transport.request(
                    self, host, handler, request_body, verbose=0)
            raise
        except xmlrpclib.Fault, e:
            if e.faultCode == ERROR_CODE:
                raise LdtpExecutionError(e.faultString)
            else:
                raise e

    def __del__(self):
        self.kill_daemon()

    def kill_daemon(self):
        try:
            self._daemon.kill()
        except AttributeError:
            pass

_client = LdtpClient('http://localhost:4118')
