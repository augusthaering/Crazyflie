

# umfrangreiche Bewegung der Drohnen
# funktioniert nicht wirklich
# # die Grenzen liegen außerhalb des Erkennungsfeld des Lighthouse Systems


import logging
import sys
import time
import threading

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

URI1 = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E704')
URI2 = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E708')

HEIGHT_1 = 0.7
HEIGHT_2 = 0.6
MOVE_DURATION = 1
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

def flight_routine(scf, start, waypoints, repeat=1):
    stabilize_and_takeoff(scf, start[0], start[1], start[2])
    current = start
    for _ in range(repeat):
        for x, y, z in waypoints:
            target = (x, y, z)
            fly_to_position(scf, current, target)
            hover(scf, x, y, z)
            current = target
    return current

def fly_simultaneously(scf1, scf2):
    start_pos_1 = (0.5, 0.0, 1.0)
    start_pos_2 = (1.5, 0.0, 1.0)

    waypoints_1 = [
        (1.0, 0.0, 1.0),
        (1.5, -0.5, 1.3),
        (1.0, -1.0, 1.1),
        (0.5, -0.5, 0.9),
        (0.0, -1.0, 1.2),
        (0.0, 0.0, 1.0),
    ]

    waypoints_2 = [
        (1.0, 0.0, 0.9),
        (0.5, -0.5, 1.2),
        (1.0, -1.0, 1.0),
        (1.5, -0.5, 1.4),
        (2.0, -1.0, 1.2),
        (2.0, 0.0, 1.0),
    ]

    result = {}

    def routine1():
        result['end1'] = flight_routine(scf1, start_pos_1, waypoints_1, repeat=2)

    def routine2():
        result['end2'] = flight_routine(scf2, start_pos_2, waypoints_2, repeat=2)

    thread1 = threading.Thread(target=routine1)
    thread2 = threading.Thread(target=routine2)

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    return result['end1'], result['end2']

# Hauptteil anpassen:
if __name__ == '__main__':
    cflib.crtp.init_drivers()
    with SyncCrazyflie(URI1, cf=Crazyflie(rw_cache='./cache')) as scf1, \
         SyncCrazyflie(URI2, cf=Crazyflie(rw_cache='./cache')) as scf2:
        scf1.cf.platform.send_arming_request(True)
        scf2.cf.platform.send_arming_request(True)
        time.sleep(0.2)

        if not check_lighthouse_system(scf1) or not check_lighthouse_system(scf2):
            sys.exit(1)

        end1, end2 = fly_simultaneously(scf1, scf2)

        land(scf1, end1[0], end1[1], end1[2])
        land(scf2, end2[0], end2[1], end2[2])

        print("Both drones have completed their routines.")
