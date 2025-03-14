import logging
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

# URI zur Crazyflie-Drohne
URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

# Höhe, in der die Drohne schweben soll
DEFAULT_HEIGHT = 0.5

# Loggen von Fehlern
logging.basicConfig(level=logging.ERROR)

def take_off_and_hover(scf):
    """Lässt die Drohne für 5 Sekunden in der Luft schweben."""
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        time.sleep(5)  # 5 Sekunden schweben
        mc.stop()  # Stoppt die Bewegung und landet

if __name__ == '__main__':
    # Initialisiere die Treiber für die Crazyflie
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        # Arming der Drohne
        scf.cf.platform.send_arming_request(True)
        time.sleep(1.0)

        take_off_and_hover(scf)  # Schwebe für 5 Sekunden
