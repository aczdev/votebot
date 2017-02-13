import psutil
from stem import Signal
from stem.control import Controller
import stem.process
from time import sleep
from urllib3.contrib.socks import SOCKSProxyManager


def kill_tor(tor_path='./tor'):
    """Finds a name of the TOR instance and kills it"""
    for proc in psutil.process_iter():
        # Get only the application's name from TOR_PATH
        if proc.name() == tor_path.split('/')[-1]:
            proc.kill()


class TorUnit(object):
    def __init__(self, tor_path, listen_port, control_port):
        self.listen_port = listen_port
        self.control_port = control_port
        self.tor_process = stem.process.launch_tor_with_config(
            tor_cmd=tor_path,
            config={
                'SocksPort': str(listen_port),
                'ControlPort': str(control_port),
            },
        )

    def __del__(self):
        self.tor_process.kill()

    def new_tor_identity(self, sleep_duration=10):
        """Sends a NEWNYM signal to TOR controller to change current exit node"""
        with Controller.from_port(port=self.control_port) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
        sleep(sleep_duration)

    def check_tor_ip(self):
        """Returns a string with IP address obtained from ifconfig.co webpage"""
        http = SOCKSProxyManager('socks5://localhost:%d/' % self.listen_port)
        # rstrip() to remove newline at the end
        ip = http.request('GET', 'http://ifconfig.co/ip').data.rstrip()
        return str(ip.decode("UTF-8"))
