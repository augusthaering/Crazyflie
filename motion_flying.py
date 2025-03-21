# -*- coding: utf-8 -*-
import logging
import sys
import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E706')
DEFAULT_HEIGHT = 0.7

deck_attached_event = Event()
logging.basicConfig(level=logging.ERROR)
position_estimate = [0, 0, 0]


def log_pos_callback(timestamp, data, logconf):
    global position_estimate
    position_estimate[0] = data['stateEstimate.x']
    position_estimate[1] = data['stateEstimate.y']
    position_estimate[2] = data['stateEstimate.z']
    print(f'{position_estimate[0]:.2f} {position_estimate[1]:.2f} {position_estimate[2]:.2f}')


def param_deck_lighthouse(_, value_str):
    value = int(value_str)
    if value:
        deck_attached_event.set()
        print('[INFO] Lighthouse V2 deck is attached!')
    else:
        print('[WARN] Lighthouse V2 deck is NOT attached!')


def wait_for_estimator(cf):
    print('[INFO] Waiting for estimator to stabilize...')
    logconf = LogConfig(name='Kalman', period_in_ms=100)
    logconf.add_variable('kalman.varPX', 'float')
    logconf.add_variable('kalman.varPY', 'float')
    logconf.add_variable('kalman.varPZ', 'float')

    ready_event = Event()

    def est_callback(ts, data, logconf):
        if all(data[k] < 0.001 for k in data):
            ready_event.set()

    cf.log.add_config(logconf)
    logconf.data_received_cb.add_callback(est_callback)
    logconf.start()

    if not ready_event.wait(10):
        print('[WARN] Estimator did not stabilize in time')
    else:
        print('[OK] Estimator is stable')

    logconf.stop()


def fly_to_fixed_position(cf):
    print('[INFO] Flying to fixed position (1.0, 1.0, 0.7)...')

    cf.param.set_value('commander.enHighLevel', '1')
    time.sleep(0.1)

    cf.high_level_commander.takeoff(0.7, 2.0)
    time.sleep(3)

    cf.high_level_commander.go_to(1.0, 1.0, 0.7, 0.0, 3.0)
    print('[ACTION] Holding position...')
    time.sleep(5)

    print('[ACTION] Landing...')
    cf.high_level_commander.land(0.0, 2.0)
    time.sleep(3)


if __name__ == '__main__':
    print('[START] Init drivers...')
    cflib.crtp.init_drivers()

    print('[START] Connecting...')
    try:
        with SyncCrazyflie(URI, cf=Crazyflie()) as scf:
            print('[OK] Connected.')

            scf.cf.platform.send_arming_request(True)
            time.sleep(1)

            print('[INFO] Registering param callback...')
            scf.cf.param.add_update_callback(group='deck', name='bcLighthouse4',
                                             cb=param_deck_lighthouse)
            time.sleep(1)

            print('[INFO] Setting up position logging...')
            pos_logconf = LogConfig(name='Position', period_in_ms=100)
            pos_logconf.add_variable('stateEstimate.x', 'float')
            pos_logconf.add_variable('stateEstimate.y', 'float')
            pos_logconf.add_variable('stateEstimate.z', 'float')
            scf.cf.log.add_config(pos_logconf)
            pos_logconf.data_received_cb.add_callback(log_pos_callback)
            pos_logconf.start()

            print('[INFO] Waiting for Lighthouse deck...')
            try:
                attached = int(scf.cf.param.get_value('deck.bcLighthouse4')) == 1
            except KeyError:
                attached = False

            if attached:
                print('[INFO] Lighthouse V2 deck is attached!')
            else:
                print('[WARN] Lighthouse V2 deck not reported via param')

            wait_for_estimator(scf.cf)
            fly_to_fixed_position(scf.cf)

            print('[INFO] Stopping logging...')
            pos_logconf.stop()

    except Exception as e:
        print(f'[FATAL] Failed: {e}')
        sys.exit(1)

    print('[END] Script done.')
