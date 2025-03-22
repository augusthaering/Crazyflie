
# 3 Drohnen
# funktioniert nicht ganz, Positionsdaten sind zu nah an der Wand etc.




import logging
import sys
import time
import threading

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

URI1 = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E706')
URI2 = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E704')
URI3 = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E701')

HEIGHT_1 = 0.7
HEIGHT_2 = 0.6
HEIGHT_3 = 0.6
MOVE_DURATION = 0.07
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
        time.sleep(0.05)

def stabilize_and_takeoff(scf, x_start, y_start, height):
    print(f"Initializing position ({x_start},{y_start},0) and taking off to height {height}...")
    for _ in range(20):
        scf.cf.extpos.send_extpos(x_start, y_start, 0.0)
        time.sleep(0.05)
    for _ in range(40):
        scf.cf.commander.send_position_setpoint(x_start, y_start, height, 0.0)
        time.sleep(0.05)
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
        time.sleep(0.05)
    scf.cf.commander.send_stop_setpoint()

def flight_routine(scf, start, waypoints, height, repeat=1):
    stabilize_and_takeoff(scf, start[0], start[1], height)
    current = (start[0], start[1], height)
    for _ in range(repeat):
        for x, y in waypoints:
            target = (x, y, height)
            fly_to_position(scf, current, target)
            hover(scf, x, y, height)
            current = target
    return current

def fly_simultaneously(scf1, scf2, scf3):
    start_pos_1 = (0.0, 0.0)
    start_pos_2 = (1.0, 0.0)
    start_pos_3 = (1.0, -1.0)

    waypoints_1 = [
        (1.0, 0.0),
        (1.0, -1.0),
        (0.0, -1.0),
        (0.0, 0.0),
    ]

    waypoints_2 = [
        (1.0, -1.0),
        (0.0, -1.0),
        (0.0, 0.0),
        (1.0, 0.0),
    ]

    waypoints_3 = [
        (0.0, -1.0),
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, -1.0),
    ]

    result = {}

    def routine1():
        result['end1'] = flight_routine(scf1, start_pos_1, waypoints_1, HEIGHT_1, repeat=3)

    def routine2():
        result['end2'] = flight_routine(scf2, start_pos_2, waypoints_2, HEIGHT_2, repeat=3)

    def routine3():
        result['end3'] = flight_routine(scf3, start_pos_3, waypoints_3, HEIGHT_3, repeat=3)

    threads = [
        threading.Thread(target=routine1),
        threading.Thread(target=routine2),
        threading.Thread(target=routine3)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return result['end1'], HEIGHT_1, result['end2'], HEIGHT_2, result['end3'], HEIGHT_3

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    with SyncCrazyflie(URI1, cf=Crazyflie()) as scf1, \
         SyncCrazyflie(URI2, cf=Crazyflie()) as scf2, \
         SyncCrazyflie(URI3, cf=Crazyflie()) as scf3:

        scf1.cf.platform.send_arming_request(True)
        scf2.cf.platform.send_arming_request(True)
        scf3.cf.platform.send_arming_request(True)
        time.sleep(0.2)

        if not check_lighthouse_system(scf1) or not check_lighthouse_system(scf2) or not check_lighthouse_system(scf3):
            sys.exit(1)

        end1, h1, end2, h2, end3, h3 = fly_simultaneously(scf1, scf2, scf3)

        land(scf1, end1[0], end1[1], h1)
        land(scf2, end2[0], end2[1], h2)
        land(scf3, end3[0], end3[1], h3)

        print("All drones have completed their routines.")
