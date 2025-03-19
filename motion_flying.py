import logging
import sys
import time
import math

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

# URI für die Drohne mit "05" am Ende
URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E705')

# Flugparameter
DEFAULT_HEIGHT = 0.5  # Flughöhe in Metern
RADIUS = 0.5  # Kreisradius in Metern
STEPS = 20  # Anzahl der Punkte für den Kreis
SPEED = 2  # Geschwindigkeit der Bewegung (höher = schneller)

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

def perform_circle_movement(scf):
    """ Bewegt die Drohne in einer Kreisformation """
    print(f"Performing a circular motion with radius {RADIUS}m...")

    for i in range(STEPS):
        angle = (i / STEPS) * 2 * math.pi  # Winkel in Radiant
        x = RADIUS * math.cos(angle)
        y = RADIUS * math.sin(angle)

        print(f"Moving to x={x:.2f}, y={y:.2f}, height={DEFAULT_HEIGHT}")
        scf.cf.commander.send_position_setpoint(x, y, DEFAULT_HEIGHT, 0.0)
        time.sleep(SPEED / STEPS)

    print("Circle complete. Hovering for 2 seconds...")
    time.sleep(2)

def return_to_start(scf):
    """ Rückkehr zur Startposition """
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
        perform_circle_movement(scf)
        return_to_start(scf)
        land_safely(scf)
