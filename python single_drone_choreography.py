import time
import math
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

# URI für die einzelne Drohne
URI = "radio://0/80/2M/E7E7E7E705"

# Flugparameter
RADIUS = 0.5  # Radius des Kreises in Metern
HEIGHT = 1.0  # Flughöhe in Metern
SPEED = 1.5   # Geschwindigkeit der Bewegung
STEPS = 20    # Anzahl der Positionen im Kreis

def power_on_and_arm(scf):
    """ Aktiviert den Brushless-Crazyflie und setzt ihn in den ARMED-Zustand. """
    cf = scf.cf
    print(f"Powering on {scf._link_uri}...")

    # Power-Up-Sequenz
    cf.param.set_value("motorPowerSet.enable", "1")  
    time.sleep(1)  # Warte kurz, damit das System sich initialisiert

    # Arming aktivieren (wichtig für Brushless)
    cf.param.set_value("motorPowerSet.arm", "1")
    print(f"{scf._link_uri} is armed.")

def takeoff(scf, height):
    """ Startet die Drohne und steigt auf die angegebene Höhe. """
    cf = scf.cf
    print(f"Takeoff: {scf._link_uri}")
    cf.commander.send_position_setpoint(0.0, 0.0, height, 0.0)
    time.sleep(3)

def land(scf):
    """ Landet die Drohne sicher und deaktiviert die Motoren. """
    cf = scf.cf
    print(f"Landing: {scf._link_uri}")
    cf.commander.send_position_setpoint(0.0, 0.0, 0.2, 0.0)
    time.sleep(2)
    cf.commander.send_position_setpoint(0.0, 0.0, 0.0, 0.0)
    time.sleep(1)
    cf.commander.send_stop_setpoint()

    # Disarm (nach dem Landen)
    cf.param.set_value("motorPowerSet.arm", "0")
    cf.param.set_value("motorPowerSet.enable", "0")
    print(f"{scf._link_uri} is disarmed.")

def circle_movement(scf):
    """ Bewegt die Drohne in einer Kreisformation. """
    cf = scf.cf

    for i in range(STEPS):
        angle = (i / STEPS) * 2 * math.pi
        x = RADIUS * math.cos(angle)
        y = RADIUS * math.sin(angle)

        print(f"Drohne {scf._link_uri} → Position: x={x:.2f}, y={y:.2f}, Höhe={HEIGHT}")
        cf.commander.send_position_setpoint(x, y, HEIGHT, 0.0)
        time.sleep(SPEED / STEPS)

def execute_flight():
    """ Führt die gesamte Choreografie aus. """
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache="./cache")) as scf:
        power_on_and_arm(scf)
        takeoff(scf, HEIGHT)
        circle_movement(scf)
        land(scf)

if __name__ == "__main__":
    execute_flight()
