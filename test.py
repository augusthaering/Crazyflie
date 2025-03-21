import logging
import sys
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E706')

DEFAULT_HEIGHT = 0.3
MOVE_DURATION = 4.0
MOVE_STEPS = 80

logging.basicConfig(level=logging.ERROR)

def check_lighthouse_system(scf):
    print("Checking Lighthouse V2 setup...")
    system_type = scf.cf.param.get_value("lighthouse.systemType")
    print(f"Lighthouse system type: {system_type}")
    if int(system_type) == 2:
        print("✅ Lighthouse V2 detected!")
        return True
    else:
        print("❌ Lighthouse V2 NOT detected!")
        return False

def stabilize_and_takeoff(scf):
    print("Initializing position (0,0,0)...")
    for _ in range(20):
        scf.cf.extpos.send_extpos(0.0, 0.0, 0.0)
        time.sleep(0.1)
    print("Taking off to default height...")
    for _ in range(40):
        scf.cf.commander.send_position_setpoint(0.0, 0.0, DEFAULT_HEIGHT, 0.0)
        time.sleep(0.1)
    print("Hovering for 2 seconds...")
    hover(scf, 0.0, 0.0, DEFAULT_HEIGHT)

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
    return target

def hover(scf, x, y, z, duration=2.0):
    steps = int(duration / 0.1)
    for _ in range(steps):
        scf.cf.commander.send_position_setpoint(x, y, z, 0.0)
        time.sleep(0.1)

def fly_to_positions(scf):
    positions = [
        (2.0, 0.0, DEFAULT_HEIGHT),
        (2.0, 2.0, DEFAULT_HEIGHT),
        (0.0, 2.0, DEFAULT_HEIGHT),
    ]
    current_pos = (0.0, 0.0, DEFAULT_HEIGHT)
    for idx, pos in enumerate(positions):
        print(f"Flying to position {idx + 1}: x={pos[0]}, y={pos[1]}, z={pos[2]}")
        current_pos = fly_to_position(scf, current_pos, pos)
        print("Hovering at position for 2 seconds...")
        hover(scf, *pos)
    return current_pos

def return_to_start(scf, current_pos):
    print("Returning to start position (0,0)...")
    fly_to_position(scf, current_pos, (0.0, 0.0, DEFAULT_HEIGHT))
    print("Hovering for 2 seconds before landing...")
    hover(scf, 0.0, 0.0, DEFAULT_HEIGHT)

def land_safely(scf):
    print("Landing...")
    for i in range(40):
        height = DEFAULT_HEIGHT * (1 - i / 40)
        scf.cf.commander.send_position_setpoint(0.0, 0.0, height, 0.0)
        time.sleep(0.1)
    scf.cf.commander.send_stop_setpoint()
    print("Landed safely.")

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        scf.cf.platform.send_arming_request(True)
        time.sleep(1.0)
        if not check_lighthouse_system(scf):
            sys.exit(1)
        stabilize_and_takeoff(scf)
        current = fly_to_positions(scf)
        return_to_start(scf, current)
        land_safely(scf)
