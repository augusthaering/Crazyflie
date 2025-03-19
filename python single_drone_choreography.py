from cflib.crazyflie import Crazyflie
from cflib.crtp import init_drivers

init_drivers()
cf = Crazyflie()
cf.open_link("radio://0/80/2M")  # Passe den URI an