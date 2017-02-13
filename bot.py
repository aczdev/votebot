from bs4 import BeautifulSoup
from datetime import datetime
from PyQt5.QtCore import *
import re
import requests
from tornado import TorUnit, kill_tor

# (TODO): Make link editable from application GUI
LINK = 'http://www.radiowroclaw.pl/pools/vote/91/1102/5'


class BotThread(QThread):
    """QThread class containing all the bot operations made in a thread"""
    def __init__(self, tor_path, listen_port, control_port):
        super().__init__()
        self.running = True
        self.tor_path = tor_path
        self.listen_port = listen_port
        self.control_port = control_port
        try:
            self.tor = TorUnit(self.tor_path, self.listen_port, self.control_port)
        except OSError:
            kill_tor(self.tor_path)
            self.tor = TorUnit(self.tor_path, self.listen_port, self.control_port)

    count_signal = pyqtSignal(int, int)
    log_signal = pyqtSignal(str)
    ip_signal = pyqtSignal(str)

    def log(self, message, timestamp=True):
        """Prepares a log string to be emitted by adding a timestamp and a message"""
        if timestamp:
            log = datetime.now().strftime("[%H:%M:%S] ") + message
        else:
            log = message
        return log

    def stop(self):
        self.running = False

    def run(self):
        """Default action after launching the thread"""
        self.log_signal.emit(self.log("TOR has been turned on. Please wait..."))

        start_ip = self.tor.check_tor_ip()
        self.log_signal.emit(self.log("Your current IP: " + start_ip))
        self.ip_signal.emit(start_ip)

        while self.running:
            try:
                self.vote(self.tor, self.listen_port)
            except requests.ConnectionError:
                self.log_signal.emit(self.log("Something is screwed with the connection! Getting a new identity..."))
                self.tor.new_tor_identity()
                self.count_signal.emit(0, 1)

    def vote(self, tor_instance, listen_port):
        """Sends a GET request to the voting page, reads the page result and notes actions"""
        proxy = 'socks5://localhost:' + str(listen_port)
        r = requests.get(LINK, proxies={'http': proxy})

        if r.status_code != 200:
            status = 'Could not connect to the voting site!'
            self.log_signal.emit(self.log(status))
            raise requests.ConnectionError(status)

        soup = BeautifulSoup(r.content, "html.parser")
        msg = str(soup.find("div", attrs={"class": "message", "id": "poolMessage"}))

        if 'nie zapisano' in msg or 'nie może' in msg:
            self.log_signal.emit(self.log("Radio has banned our IP address! Changing the identity..."))
            tor_instance.new_tor_identity(sleep_duration=3)
            # Give +1 to identity changes
            self.count_signal.emit(0, 1)

            new_ip = self.tor.check_tor_ip()
            status = self.log('New identity IP address: ' + new_ip)
            self.log_signal.emit(status)
            self.ip_signal.emit(new_ip)

        else:
            status = self.log('Gave five stars in the poll. Per aspera ad astra!')
            self.log_signal.emit(status)
            # Give +1 to votes count number
            self.count_signal.emit(1, 0)

        # (TODO): Display it in separate text boxes
        votes_log = self.log(self._voting_status(soup))
        self.log_signal.emit(votes_log)

    def _voting_status(self, soup):
        """Return a list with all the poll names, ratings and vote numbers. Hidden function."""
        elements = soup.find_all("div", attrs={"class": "elem"})
        voting_status = []

        for i in elements:
            # Read a name of a theatre
            theatre = i.find("div", attrs={"class": "name"}).contents

            # Regular expression to detect decimal and float numbers
            numbers_regex = r'(?:\d*\.)?\d+'
            paragraphs = i.find_all("p")

            votes_parags = str(paragraphs[0])
            votes_count = re.findall(numbers_regex, votes_parags)

            note_parags = str(paragraphs[1])
            note = re.findall(numbers_regex, note_parags)

            theatre_status = str(theatre) + '\t' + str(votes_count) + '\t' + str(note)
            voting_status.append(theatre_status)

        return voting_status