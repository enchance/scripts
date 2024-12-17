import os
import sys
import re
import logging
import subprocess
import configparser
from typing import Dict, Tuple

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
        self.setup_logging()

    def setup_logging(self):
        log_file = self.config.get('General', 'log_file')
        handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=2*1024*1024, backupCount=5
        )
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[handler]
        )

    def get_temperatures(self) -> Dict[str, float]:
        try:
            output = subprocess.check_output(['sensors'], text=True)

            return {
                'cpu': float(re.search(r'Tctl:\s*\+?([\d.]+)°C', output).group(1)),
                'gpu': float(re.search(r'edge:\s*\+?([\d.]+)°C', output).group(1)),
                'nvme': float(re.search(r'Composite:\s*\+?([\d.]+)°C', output).group(1))
            }
        except Exception as e:
            logging.error(f"Temperature fetch error: {e}")
            return {'cpu': -1, 'gpu': -1, 'nvme': -1}

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
            'cpu': QtWidgets.QLabel("CPU: N/A"),
            'gpu': QtWidgets.QLabel("GPU: N/A"),
            'nvme': QtWidgets.QLabel("NVME: N/A")
        }

        for label in self.labels.values():
            label.setStyleSheet("""
                color: white;
                background-color: rgba(0, 0, 0, 150);
                padding: 5px;
                border-radius: 5px;
            """)
            label.setFont(QtGui.QFont('Monospace', 10))
            layout.addWidget(label)

        self.setLayout(layout)
        self.setGeometry(QtWidgets.QDesktopWidget().width() - 250, 50, 230, 150)

    def _setup_timer(self):
        interval = int(self.config.get('General', 'poll_interval')) * 1000
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_temperatures)
        self.timer.start(interval)

    def update_temperatures(self):
        temps = self.monitor.get_temperatures()

        for key, temp in temps.items():
            color = self._get_temp_color(key, temp)
            self.labels[key].setText(f"{key.upper()}: {temp}°C")
            self.labels[key].setStyleSheet(f"""
                color: white;
                background-color: {color};
                padding: 5px;
                border-radius: 5px;
            """)

    def _get_temp_color(self, component: str, temp: float) -> str:
        # Implement color logic based on thresholds
        pass  # TODO: Implement color selection logic

def main():
    app = QtWidgets.QApplication(sys.argv)
    config = TemperatureConfig()
    overlay = TemperatureOverlay(config)
    overlay.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()