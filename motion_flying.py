hthouse etc. implementieren, das ist der aktuelle Basiscode: import logging
import sys
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E705')
DEFAULT_HEIGHT = 0.5

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
    """ Initialisiert die Position und führt einen stabilen Takeoff durch """
    print("Initializing position (0,0,0)...")
    for _ in range(20):
        scf.cf.extpos.send_extpos(0.0, 0.0, 0.0)
        time.sleep(0.1)

    print("Taking off to default height...")
    for _ in range(40):  # Langsam steigen für Stabilität
        scf.cf.commander.send_position_setpoint(0.0, 0.0, DEFAULT_HEIGHT, 0.0)
        time.sleep(0.1)

    print("Hovering for 2 seconds...")
    time.sleep(2)  # Warten, bis sich die Drohne stabilisiert

def move_stably(scf):
    """ Führt langsame, kontrollierte Bewegungen aus """
    print("Moving to absolute position (0.5m, 0.5m)...")
    for _ in range(50):  # Langsames Bewegen
        scf.cf.commander.send_position_setpoint(20, 1, DEFAULT_HEIGHT, 0.0)
        time.sleep(0.1)

    print("Hovering for 2 seconds...")
    time.sleep(2)

    print("Returning to start position")
    for _ in range(50):
        scf.cf.commander.send_position_setpoint(0.0, 0.0, DEFAULT_HEIGHT, 0.0)
        time.sleep(0.1)

    print("Hovering for 2 seconds before landing...")
    time.sleep(2)

def land_safely(scf):
    """ Führt eine langsame Landung durch """
    print("Landing...")
    for _ in range(40):  # Langsame Landung
        scf.cf.commander.send_position_setpoint(0.0, 0.0, 0.1, 0.0)
        time.sleep(1)

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
        move_stably(scf)
        land_safely(scf)