#!/usr/bin/env python3

import os
import sys
import time
import fcntl
import logging
import sqlite3
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError


# Ensure config directory exists
APPNAME = 'envyfanspeed'
CONFIG_DIR = Path.home() / '.config' / APPNAME
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Paths
DB_PATH = CONFIG_DIR / 'fanspeed.db'
LOG_PATH = CONFIG_DIR / f'{APPNAME}.log'
LOCK_FILE = CONFIG_DIR / f'{APPNAME}.lock'

# Configure logging
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)

# SQLAlchemy Setup
Base = declarative_base()


class FanSpeedLog(Base):
    __tablename__ = 'fan_speed_logs'
    id = sa.Column(sa.Integer, primary_key=True)
    timestamp = sa.Column(sa.DateTime, default=sa.func.now())
    temperature = sa.Column(sa.Float)
    fan_speed = sa.Column(sa.Integer)


def create_engine_and_session():
    engine = sa.create_engine(f'sqlite:///{DB_PATH}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session()


def log_fan_data(temperature: float, fan_speed: int):
    try:
        _, session = create_engine_and_session()
        log_entry = FanSpeedLog(temperature=temperature, fan_speed=fan_speed)
        session.add(log_entry)
        session.commit()
    except SQLAlchemyError as e:
        logging.error(f"Database logging error: {e}")


def sigmoid_fan_speed(temperature: float, max_speed: int = 90) -> int:
    """Simple sigmoid-like fan speed adjustment"""
    base_temp = 60
    scale = 10
    midpoint = 75

    normalized_temp = (temperature - midpoint) / scale
    fan_speed = int(max_speed / (1 + pow(2.718, -normalized_temp)))
    # print(temperature, normalized_temp, fan_speed, sep=':')

    return min(max(fan_speed, 20), max_speed)


def get_gpu_temperature() -> Optional[float]:
    try:
        result = subprocess.run(
            ['nvidia-settings', '-q', 'GPUCoreTemp', '-t'],
            capture_output=True, text=True, check=True
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        logging.error(f"Temperature retrieval error: {e}")
        return None


def set_fan_speed(speed: int):
    try:
        subprocess.run(
            ['nvidia-settings', '-a', f'[gpu:0]/GPUFanControlState=1', f'-a', f'[fan:0]/GPUTargetFanSpeed={speed}'],
            check=True
        )
        logging.info(f"Fan speed set to {speed}%")
    except subprocess.CalledProcessError as e:
        logging.error(f"Fan speed setting error: {e}")


def parse_arguments():
    parser = argparse.ArgumentParser(description='NVIDIA GPU Fan Speed Control')
    parser.add_argument('-V', '--version', action='version', version='1.0.0')
    parser.add_argument('-d', '--detach', action='store_true', help='Run in background')
    parser.add_argument('-s', '--speed', choices=['slow', 'medium', 'fast'], default='medium')
    parser.add_argument('-m', '--max', type=int, default=90, help='Maximum fan speed')
    parser.add_argument('-c', '--cooldown', type=int, default=5, help='Cooldown between adjustments')
    parser.add_argument('--dry-run', action='store_true', help='Check temperature without changing fan speed')
    parser.add_argument('--no-delete', action='store_true', help='Prevent database deletion')
    parser.add_argument('--no-notify', action='store_true', help='Disable system notifications')

    return parser.parse_args()


def main():
    # Ensure single instance
    with open(LOCK_FILE, 'w') as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, BlockingIOError):
            logging.error("Another instance is already running.")
            sys.exit(1)

        try:
            args = parse_arguments()

            # Clean previous database if not prevented
            if not args.no_delete and DB_PATH.exists():
                DB_PATH.unlink()

            while True:
                temperature = get_gpu_temperature()
                if temperature is None:
                    logging.error("Could not retrieve GPU temperature")
                    break

                fan_speed = sigmoid_fan_speed(temperature, args.max)
                # print(temperature, fan_speed, sep=' : ')
                log_fan_data(temperature, fan_speed)

                if not args.dry_run:
                    set_fan_speed(fan_speed)

                time.sleep(args.cooldown)

        except Exception as e:
            logging.critical(f"Unhandled exception: {e}")
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


if __name__ == '__main__':
    main()
