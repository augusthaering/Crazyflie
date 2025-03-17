import cflib.crtp
from cflib.crazyflie import Crazyflie

def deck_status_callback(name, value):
    print(f"{name}: {value}")

cflib.crtp.init_drivers(enable_debug_driver=False)
cf = Crazyflie(rw_cache="./cache")

link_uri = "radio://0/80/2M"  # Passe die URI an, falls nötig
cf.open_link(link_uri)

cf.param.add_update_callback(group="deck", name="bcLighthouse", cb=deck_status_callback)
