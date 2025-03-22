
# ich weiß es nicht mehr

import logging
import sys
import time
import threading

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

URI1 = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E706')
URI2 = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E708')

DEFAULT_HEIGHT_1 = 0.3
DEFAULT_HEIGHT_2 = 1.2
MOVE_DURATION = 0.2
MOVE_STEPS = 80

logging.basicConfig(level=logging.ERROR)

def check_lighthouse_system(scf):
    print("Checking Lighthouse V2 setup...")
    system_type = scf.cf.param.get_value("lighthouse.systemType")
    print(f"Lighthouse system type: {system_type}")
    return int(system_type) == 2

def hover(scf, x, y, z, duration=2.0):
    steps = int(duration / 0.1)
    for _ in range(steps):
        scf.cf.commander.send_position_setpoint(x, y, z, 0.0)
        time.sleep(0.1)

def stabilize_and_takeoff(scf, x_start, y_start, height):
    print(f"Initializing position ({x_start},{y_start},0) and taking off to height {height}...")
    for _ in range(20):
        scf.cf.extpos.send_extpos(x_start, y_start, 0.0)
        time.sleep(0.1)
    for _ in range(40):
        scf.cf.commander.send_position_setpoint(x_start, y_start, height, 0.0)
        time.sleep(0.1)
    hover(scf, x_start, y_start, height)

def fly_to_position(scf, start, target):
    dx = (target[0] - start[0]) / MOVE_STEPS
    dy = (target[1] - start[1]) / MOVE_STEPS
    dz = (target[2] - start[2]) / MOVE_STEPS
    for i in range(MOVE_STEPS):
        x = start[0] + dx * i
        y = start[1] + dy * i
        z = start[2] + dz * i
        scf.cf.commander.send_position_setpoint(x, y, z, 0.0)
        time.sleep(MOVE_DURATION / MOVE_STEPS)

def land(scf, x, y, start_height):
    for i in range(40):
        z = start_height * (1 - i / 40)
        scf.cf.commander.send_position_setpoint(x, y, z, 0.0)
        time.sleep(0.1)
    scf.cf.commander.send_stop_setpoint()

def flight_routine(scf, start, end, height):
    stabilize_and_takeoff(scf, start[0], start[1], height)
    fly_to_position(scf, (start[0], start[1], height), (end[0], end[1], height))
    hover(scf, end[0], end[1], height)
    land(scf, end[0], end[1], height)

def fly_simultaneously(scf1, scf2):
    start_pos_1 = (0.0, 0.0)
    start_pos_2 = (0.5, 0.0)
    target_pos_1 = (0.5, 0.0)
    target_pos_2 = (1.0, 0.0)

    thread1 = threading.Thread(target=flight_routine, args=(scf1, start_pos_1, target_pos_1, DEFAULT_HEIGHT_1))
    thread2 = threading.Thread(target=flight_routine, args=(scf2, start_pos_2, target_pos_2, DEFAULT_HEIGHT_2))

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    with SyncCrazyflie(URI1, cf=Crazyflie(rw_cache='./cache')) as scf1, \
         SyncCrazyflie(URI2, cf=Crazyflie(rw_cache='./cache')) as scf2:
        scf1.cf.platform.send_arming_request(True)
        scf2.cf.platform.send_arming_request(True)
        time.sleep(1.0)

        if not check_lighthouse_system(scf1) or not check_lighthouse_system(scf2):
            sys.exit(1)

        fly_simultaneously(scf1, scf2)
        print("Both drones have completed their routines.")
