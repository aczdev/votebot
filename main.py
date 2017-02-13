###
# Votebot (version 0.9.4) by Adam Cz.
#
# A small proof-of-concept bot to show an automation process of voting
# on a radio page with usage of threading and TOR process. It was written
# as fast as possible, so it can still contain a lot of minor bugs.
#
# Remember to edit TOR_PATH global at the beginning, depending on which OS
# you are using! You can download TOR client from https://www.torproject.org/
#
###

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from tornado import kill_tor
from bot import BotThread

# (TODO):   A QFileDialog to select a path to TOR client instead of this
#           quick and dirty hardcode. Same with listening and control ports.
TOR_PATH = './Tor/tor.exe'
LISTEN = 21337
CONTROL = 31337


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.console = QTextEdit()
        self.ip_display = QLineEdit("")
        self.vote_counter = QLineEdit("0")
        self.id_counter = QLineEdit("0")

        try:
            self.initUI()
        except (OSError, AttributeError):
            self.kill_tor()
            self.initUI()

        self.id_count = 0
        self.vote_count = 0
        self.bot_thread = None

    def initUI(self):
        # (TODO): Make the GUI in a separate file (and by QtDesigner)

        # Button groupbox
        start = QPushButton("Start")
        start.clicked.connect(self.startClicked)

        stop = QPushButton("Stop")
        stop.clicked.connect(self.stopClicked)

        # An old concept that will be scripted in the future
        restart_tor = QPushButton("Restart TOR")
        restart_tor.setEnabled(False)
        # restart_tor.clicked.connect(self.killClicked)

        button_box = QHBoxLayout()
        button_box.setSpacing(10)

        button_box.addWidget(start)
        button_box.addWidget(stop)
        button_box.addWidget(restart_tor)

        button_group = QGroupBox("Bot control")
        button_group.setLayout(button_box)

        # Counter groupbox
        self.vote_counter.setReadOnly(True)
        vote_counter_title = QLabel("Vote count: ")

        self.id_counter.setReadOnly(True)
        id_counter_title = QLabel("Changed ID count: ")

        self.ip_display.setReadOnly(True)
        ip_title = QLabel("Current IP: ")

        counter_box = QHBoxLayout()
        counter_box.addWidget(vote_counter_title)
        counter_box.addWidget(self.vote_counter)
        counter_box.addWidget(id_counter_title)
        counter_box.addWidget(self.id_counter)
        counter_box.addWidget(ip_title)
        counter_box.addWidget(self.ip_display)

        counter_group = QGroupBox("Counts")
        counter_group.setLayout(counter_box)

        # Console groupbox
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background: black; color: lime; font-size: 11px")
        console_box = QHBoxLayout()
        console_box.addWidget(self.console)

        console_group = QGroupBox("Log console")
        console_group.setLayout(console_box)

        # Main grid and central layout
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(button_group, 1, 0)
        grid.addWidget(counter_group, 2, 0)
        grid.addWidget(console_group, 3, 0)

        central_widget = QWidget()
        central_widget.setLayout(grid)

        # Main window options
        self.setLayout(grid)
        self.statusBar().showMessage('Ready to launch')

        self.setCentralWidget(central_widget)
        self.setGeometry(350, 200, 600, 400)
        self.setWindowTitle('Votebot 0.9.4')
        self.show()

    def startClicked(self):
        self.statusBar().showMessage('Bot is running!')
        self.console.append("Connecting to TOR!")

        self.bot_thread = BotThread(TOR_PATH, LISTEN, CONTROL)
        self.bot_thread.count_signal.connect(self.catch_count_signal)
        self.bot_thread.log_signal.connect(self.catch_log_signal)
        self.bot_thread.ip_signal.connect(self.catch_ip_signal)

        self.bot_thread.running = True
        self.bot_thread.start()

    def stopClicked(self):
        self.statusBar().showMessage('STOP!')
        self.bot_thread.stop()
        self.console.append("Bot has been stopped by user!")

    @pyqtSlot(int, int)
    def catch_count_signal(self, vote, id):
        self.vote_count += vote
        self.id_count += id

        self.vote_counter.setText(str(self.vote_count))
        self.id_counter.setText(str(self.id_count))

    @pyqtSlot(str)
    def catch_ip_signal(self, ip_string):
        self.ip_display.setText(ip_string)

    @pyqtSlot(str)
    def catch_log_signal(self, console_msg):
        self.console.append(console_msg)

    def closeEvent(self, event):
        # Sometimes user will click Stop button before
        # closing the app, hence this exception below.
        try:
            kill_tor(TOR_PATH)
        except AttributeError:
            pass
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
