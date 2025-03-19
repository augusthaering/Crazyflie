import logging
import sys
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

# URI für die Drohne mit "05" am Ende
URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E705')

# Flugparameter
DEFAULT_HEIGHT = 0.5  # Flughöhe in Metern
MOVEMENT_DISTANCE = 0.5  # Maximale Bewegung nach links/rechts in Metern
STEPS = 5  # Anzahl der Links-Rechts-Bewegungen
SPEED = 1  # Geschwindigkeit der Bewegung (höher = schneller)

logging.basicConfig(level=logging.ERROR)

def check_lighthouse_system(scf):
    """ Überprüft, ob das Lighthouse V2 Tracking aktiv ist """
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

def left_right_movement(scf):
    """ Bewegt die Drohne abwechselnd nach links und rechts """
    print(f"Performing left-right movement ({STEPS} cycles)...")

    for i in range(STEPS):
        direction = -1 if i % 2 == 0 else 1  # Abwechselnd -1 (links) und 1 (rechts)
        x = direction * MOVEMENT_DISTANCE  # Setzt x auf -0.5 oder +0.5

        print(f"Moving to x={x:.2f}, y=0.0, height={DEFAULT_HEIGHT}")
        scf.cf.commander.send_position_setpoint(x, 0.0, DEFAULT_HEIGHT, 0.0)
        time.sleep(SPEED)

    print("Returning to start position (0,0)...")
    for _ in range(40):
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
        left_right_movement(scf)
        land_safely(scf)
