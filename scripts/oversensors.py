#!/usr/bin/env python3

import os
import sys
import re
import logging
import subprocess
import configparser
from typing import Dict, List
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
    }
}


class TemperatureConfig:
    def __init__(self):
        self.config_path = os.path.expanduser('~/.config/oversensors.ini')
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        # Load defaults first
        self.config.read_dict(DEFAULT_CONFIG)

        # Attempt to read user config
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

    def get_temperatures(self) -> Dict[str, float]:
        try:
            system_temps = subprocess.check_output(['sensors'], text=True)

            return {
                'cpu': float(re.search(r'Tctl:\s*\+?([\d.]+)°C', system_temps).group(1)),
                'gpu': float(re.search(r'edge:\s*\+?([\d.]+)°C', system_temps).group(1)),
                'nvme': float(re.search(r'Composite:\s*\+?([\d.]+)°C', system_temps).group(1))
            }
        except Exception as e:
            logging.error(f"System temperature fetch error: {e}")
            return {'cpu': -1, 'gpu': -1, 'nvme': -1}

    def get_gpu_fans(self) -> List[int]:
        try:
            # Use nvidia-smi to get GPU fan speeds
            nvidia_output = subprocess.check_output(['nvidia-smi', '--query-gpu=fan.speed', '--format=csv,noheader'],
                                                    text=True)
            # Parse fan speeds, split and convert to integers
            return [int(speed.strip().rstrip(' %')) for speed in nvidia_output.split('\n') if speed.strip()]
        except Exception as e:
            logging.error(f"GPU fan speed fetch error: {e}")
            return []


class TemperatureOverlay(QtWidgets.QWidget):
    def __init__(self, config: TemperatureConfig):
        super().__init__()
        self.config = config
        self.monitor = TemperatureMonitor(config)

        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self):
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint |
                            QtCore.Qt.FramelessWindowHint |
                            QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

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
            label.setFont(QtGui.QFont('Consolas', 8))
            layout.addWidget(label)

        self.setLayout(layout)
        # self.setGeometry(QtWidgets.QDesktopWidget().width() - 250, 50, 230, 200)
        self.setGeometry(QtWidgets.QDesktopWidget().width() - 50, QtWidgets.QDesktopWidget().height() - 200, 60, 100)

    def _setup_timer(self):
        interval = int(self.config.get('General', 'poll_interval')) * 1000
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_temperatures)
        self.timer.start(interval)

    def update_temperatures(self):
        temps = self.monitor.get_temperatures()
        fans = self.monitor.get_gpu_fans()

        for key, temp in temps.items():
            color = self._get_temp_color(key, temp)
            self.labels[key].setText(f"{key.upper()}: {temp}°C")
            self.labels[key].setStyleSheet(f"""
                color: white;
                background-color: {color};
                padding: 3px;
                border-radius: 5px;
            """)

        # Display GPU fan speeds
        if fans:
            fan_text = "Fans: " + " / ".join(f"{speed}%" for speed in fans)
            self.labels['fans'].setText(fan_text)

    def _get_temp_color(self, component: str, temp: float) -> str:
        # Implement color logic based on thresholds
        thresholds = {
            'cpu': (65, 75, 85),
            'gpu': (50, 65, 80),
            'nvme': (45, 60, 70)
        }

        if component not in thresholds:
            return 'rgba(100,100,100,50)'  # Neutral gray

        normal, warm, hot = thresholds[component]

        if temp < normal:
            # return 'rgba(0,255,0,150)'  # Green
            return 'rgba(188,255,0,70)'  # Green
        elif temp < warm:
            # return 'rgba(255,255,0,50)'  # Yellow
            return 'rgba(248,241,90,70)'  # Yellow
        elif temp < hot:
            # return 'rgba(255,165,0,50)'  # Orange
            return 'rgba(255,209,83,70)'  # Orange
        else:
            # return 'rgba(255,0,0,50)'  # Red
            return 'rgba(255,115,83,70)'  # Red

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    # def mouseReleaseEvent(self, event):
    #     if event.button() == QtCore.Qt.LeftButton:
    #         self._drag_pos = None
    #         event.accept()


def main():
    setproctitle('oversensors')
    app = QtWidgets.QApplication(sys.argv)
    config = TemperatureConfig()
    overlay = TemperatureOverlay(config)
    overlay.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
