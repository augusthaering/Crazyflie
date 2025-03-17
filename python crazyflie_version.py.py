from cflib.crazyflie import Crazyflie
from cflib.crtp import crtp

# Verbindung zur Crazyflie herstellen
crtp.init_drivers()
cf = Crazyflie(rw_cache='./cache')

# Verbindung aufbauen
cf.open_link('radio://0/80/2M')

# Firmware Version abfragen
version = cf.get_version()
print(f"Firmware Version: {version}")
cf.close_link()
