#!/usr/bin/env python3

import os
import sys
import fcntl
import re
import logging
import subprocess
import configparser
from logging.handlers import RotatingFileHandler
from setproctitle import setproctitle

import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui


# Global Defaults
DEFAULT_CONFIG = {
    'General': {
        'poll_interval': '3',
        'log_file': '/var/log/oversensors.log'
    },
    'Thresholds': {
        'cpu_normal': '65',
        'cpu_warm': '75',
        'cpu_hot': '85',
        'gpu_normal': '50',
        'gpu_warm': '65',
        'gpu_hot': '80',
        'nvme_normal': '45',
        'nvme_warm': '60',
        'nvme_hot': '70'
    },
    'Notifications': {
        'cpu_threshold': '79',
        'gpu_threshold': '75',
        'nvme_threshold': '65'
    },
    'Display': {
        'overlay_position': 'top-right',
    }
}


class TemperatureConfig:
    def __init__(self):
        self.config_path = os.path.expanduser('~/.config/oversensors.ini')
        self.config = configparser.ConfigParser()
        self.load_config()


    def load_config(self):
        self.config.read_dict(DEFAULT_CONFIG)
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)


    def get(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)


class TemperatureMonitor:
    def __init__(self, config: TemperatureConfig):
        self.config = config
        # self.setup_logging()


    # def setup_logging(self):
    #     log_file = self.config.get('General', 'log_file')
    #     handler = RotatingFileHandler(
    #         log_file, maxBytes=2 * 1024 * 1024, backupCount=5
    #     )
    #     logging.basicConfig(
    #         level=logging.INFO,
    #         format='%(asctime)s - %(levelname)s: %(message)s',
    #         handlers=[handler]
    #     )

    @staticmethod
    def get_temperatures() -> dict[str, float]:
        try:
            system_temps = subprocess.check_output(['sensors'], text=True)

            cpu_val = float(re.search(r'Tctl:\s*\+?([\d.]+)°C', system_temps).group(1)),
            gpu_val = float(re.search(r'edge:\s*\+?([\d.]+)°C', system_temps).group(1)),
            nvme_val = float(re.search(r'Composite:\s*\+?([\d.]+)°C', system_temps).group(1))

            data = {
                'cpu': cpu_val[0],
                'gpu': gpu_val[0],
                'nvme': nvme_val,
            }
            return data
        except Exception as e:
            logging.error(f"System temperature fetch error: {e}")
            return {'cpu': -1, 'gpu': -1, 'nvme': -1}


    @staticmethod
    def get_gpu_fans() -> int:
        try:
            nvidia_output = subprocess.check_output(['nvidia-smi', '--query-gpu=fan.speed', '--format=csv,noheader'],
                                                    text=True)
            return int(nvidia_output.strip().rstrip(' %'))
        except Exception as e:
            logging.error(f"GPU fan speed fetch error: {e}")
            return -1


class TemperatureOverlay(QtWidgets.QWidget):
    def __init__(self, config: TemperatureConfig):
        super().__init__()
        self.config = config
        self.monitor = TemperatureMonitor(config)

        self._setup_ui()
        self._setup_timer()


    def _setup_ui(self):
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint |  # type: ignore
                            QtCore.Qt.FramelessWindowHint |  # type: ignore
                            QtCore.Qt.Tool)  # type: ignore
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # type: ignore

        self._create_context_menu()

        layout = QtWidgets.QVBoxLayout()
        self.labels = {
            'cpu': QtWidgets.QLabel("CPU: --"),
            'gpu': QtWidgets.QLabel("GPU: --"),
            'nvme': QtWidgets.QLabel("NVME: --"),
            'fans': QtWidgets.QLabel("Fans: --")
        }

        for label in self.labels.values():
            label.setStyleSheet("""
                color: white;
                background-color: rgba(0, 0, 0, 100);
                padding: 5px;
                border-radius: 3px;
                font-weight: bold;
            """)
            label.setFont(QtGui.QFont('Consolas', 10))
            layout.addWidget(label)

        # top-left
        xpos = 50
        ypos = 50
        if self.config.get('Display', 'overlay_position') == 'top-right':
            xpos = QtWidgets.QDesktopWidget().width() - 50
        elif self.config.get('Display', 'overlay_position') == 'bottom-right':
            xpos = QtWidgets.QDesktopWidget().width() - 50
            ypos = QtWidgets.QDesktopWidget().height() - 200
        elif self.config.get('Display', 'overlay_position') == 'bottom-left':
            ypos = QtWidgets.QDesktopWidget().height() - 200

        self.setLayout(layout)
        self.setGeometry(xpos, ypos, 60, 100)


    def _setup_timer(self):
        interval = int(self.config.get('General', 'poll_interval')) * 1000
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_temperatures)
        self.timer.start(interval)


    def update_temperatures(self):
        temps = self.monitor.get_temperatures()
        fans = self.monitor.get_gpu_fans()

        for key, temp in temps.items():
            bgcolor = self._get_temp_color(key, temp)
            if key in ['cpu', 'gpu']:
                self.labels[key].setText(f"{key.upper()}:  {temp}°C")
            else:
                self.labels[key].setText(f"{key.upper()}: {temp}°C")
            self.labels[key].setStyleSheet(self._get_stylesheet(bgcolor))

        if fans >= 0:
            fan_text = f'Fans: {fans}%'
            bgcolor = self._get_temp_color('fans', fans)
            self.labels['fans'].setText(fan_text)
            self.labels['fans'].setStyleSheet(self._get_stylesheet(bgcolor))


    @staticmethod
    def _get_stylesheet(bgcolor: str) -> str:
        return f"""
                color: white;
                background-color: {bgcolor};
                padding: 3px;
                border-radius: 5px;
            """


    def _get_temp_color(self, component: str, temp: float) -> str:
        # Implement color logic based on thresholds
        thresholds = {
            'cpu': (int(self.config.get('Thresholds', 'cpu_normal')), int(self.config.get('Thresholds', 'cpu_warm')),
                    int(self.config.get('Thresholds', 'cpu_hot'))),
            'gpu': (int(self.config.get('Thresholds', 'gpu_normal')), int(self.config.get('Thresholds', 'gpu_warm')),
                    int(self.config.get('Thresholds', 'gpu_hot'))),
            'nvme': (int(self.config.get('Thresholds', 'nvme_normal')), int(self.config.get('Thresholds', 'nvme_warm')),
                     int(self.config.get('Thresholds', 'nvme_hot'))),
            'fans': (int(self.config.get('Thresholds', 'fan_off')), int(self.config.get('Thresholds', 'fan_slow')),
                     int(self.config.get('Thresholds', 'fan_fast')))
        }

        if component not in thresholds:
            return 'rgba(100,100,100,50)'  # Neutral gray

        normal, warm, hot = thresholds[component]

        if temp < normal:
            return 'rgba(29,101,0,0.7)'  # Green
        elif temp < warm:
            return 'rgba(29,101,0,0.7)'  # Green
        elif temp < hot:
            return 'rgba(255,132,0,0.5)'  # Orange
        else:
            return 'rgba(117,0,0,0.8)'  # Red


    def _create_context_menu(self):
        self.context_menu = QtWidgets.QMenu(self)
        close_action = self.context_menu.addAction("Close")
        close_action.triggered.connect(self._close_application)


    def _close_application(self):
        QtWidgets.QApplication.instance().quit()


    def contextMenuEvent(self, event):
        self.context_menu.exec_(event.globalPos())


    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:  # noqa
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()  # noqa
            event.accept()


    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == QtCore.Qt.LeftButton:  # noqa
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    # def mouseReleaseEvent(self, event):
    #     if event.button() == QtCore.Qt.LeftButton:
    #         self._drag_pos = None
    #         event.accept()


def main():
    # process_title = DEFAULT_CONFIG.get('DEFAULT_CONFIG', 'process_title')
    process_title = 'oversensors'
    lock_file = "/tmp/oversensors.lock"

    try:
        # Open a lock file
        fp = open(lock_file, "w+")
        # Try to lock it using fcntl
        fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("Another instance of the script is already running. Exiting.")
        sys.exit(1)

    try:
        setproctitle(process_title)
        app = QtWidgets.QApplication(sys.argv)
        config = TemperatureConfig()
        overlay = TemperatureOverlay(config)
        overlay.show()
        sys.exit(app.exec_())
    finally:
        fcntl.flock(fp, fcntl.LOCK_UN)  # noqa
        fp.close()  # noqa


if __name__ == '__main__':
    main()
