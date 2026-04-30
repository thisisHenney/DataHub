import datetime
import json
import sys
import time
from pathlib import Path
from typing import Union

import numpy as np
from PySide6.QtCore import QTimer, QCoreApplication
from PySide6.QtWidgets import QMainWindow
from vtkmodules.util import numpy_support
from vtkmodules.vtkIOLegacy import vtkDataSetReader


PINTEL_IP='192.168.10.112'
PINTEL_PORT=1883
PINTEL_TOPIC_SIM = 'PVX-V30/PA-7F000001/POT/CROWD/CROWD_SIM'

import threading
import paho.mqtt.client as mqtt


class SimpleMqttPublisher:
    def __init__(self, broker_host=PINTEL_IP, broker_port=PINTEL_PORT, client_id="nf"):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client(client_id=client_id)

    def connect(self, username=None, password=None):
        if username and password:
            self.client.username_pw_set(username, password)

        self.client.connect(self.broker_host, self.broker_port)
        self.client.loop_start()  # 백그라운드 네트워크 루프 시작

    def publish(self, topic, message, qos=0, retain=False):
        """문자열을 원하는 토픽으로 송신"""
        result = self.client.publish(topic, message, qos=qos, retain=retain)
        result.wait_for_publish()  # 전송이 끝날 때까지 대기
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"[OK] Sent to {topic}: {message[:100]}...")
        else:
            print(f"[ERROR] Failed to send message. RC={result.rc}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()


class TimeVtkConverter:
    BROKER = 'localhost'
    PORT = 1883
    TOPIC = "rpi_density"

    def __init__(self):
        pass

    def make_dict(self, amount, num, time_sec, sim_type,
                  simulation_time_str, simulator_time_str, array: Union[list, str, float]):
        dict_for_json = {
            'amount_of_data': amount,
            'now_num': num,
            'data_time_sec': time_sec,
            'simulation_type': sim_type,
            'simulation_start_time': simulation_time_str,
            'simulator_start_time': simulator_time_str,
            'data_label': ['pos_x', 'pos_y', 'vel_x', 'vel_y', 'density'],
            'data': array
        }
        return dict_for_json

    def read_directory(self, folder_path: Path):
        str_list = []
        vtk_files = list(folder_path.glob('*.vtk'))
        sorted_files = sorted(vtk_files, key=lambda x: int(x.stem.split('_')[-1]))
        amount = len(sorted_files)

        simulator_time = datetime.datetime.now()        # 솔버 돌린 시간
        sr = simulator_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        simulation_time = datetime.datetime.now() - datetime.timedelta(hours=2)     # 실제 공연 시간
        st = simulation_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        for i, vtk_file in enumerate(sorted_files):
            reader = vtkDataSetReader()
            reader.SetFileName(str(vtk_file.absolute()))
            reader.Update()
            data = reader.GetOutput()
            pos = data.GetPoints().GetData()
            pos_arr = numpy_support.vtk_to_numpy(pos)
            vel = data.GetPointData().GetArray("velocity")
            vel_arr = numpy_support.vtk_to_numpy(vel)
            dens = data.GetPointData().GetArray("density")
            dens_arr = numpy_support.vtk_to_numpy(dens)
            dens_arr = dens_arr.reshape(len(dens_arr), 1)

            full_arr = np.hstack([pos_arr[:, :2], vel_arr, dens_arr]).astype(np.float64)
            valid_rows = ~np.isnan(full_arr.astype(float)).any(axis=1)
            full_arr = full_arr[valid_rows]
            full_arr = np.round(full_arr, 6)

            full_arr_str = json.dumps(full_arr.tolist())

            import gzip
            import base64
            data = full_arr_str.encode("utf-8")
            compressed = gzip.compress(data)
            b64 = base64.b64encode(compressed).decode()

            # import blosc
            # import base64
            # import time
            # start = time.perf_counter()
            # bytes_arr = full_arr.tobytes()
            # compressed_arr = blosc.compress(bytes_arr, cname='zlib')
            # # compressed_density = snappy.compress(bytes_density)
            # b64 = base64.b64encode(compressed_arr).decode("ascii")
            dict_for_json = self.make_dict(amount, i + 1, vtk_file.stem.split('_')[-1],
                                           'performing', st, sr, b64)   #
            #
            # dict_for_json = self.make_dict(amount, i+1, vtk_file.stem.split('_')[-1], full_arr.tolist())
            json_string = json.dumps(dict_for_json)
            str_list.append(json_string)

        return str_list


if __name__ == '__main__':
    tvc = TimeVtkConverter()
    str_list = tvc.read_directory(Path(r'C:\Users\nextfoam-CV-user\Downloads\Re_ [넥스트폼] 2025-09-13 공연데이터 바이너리 파일 전달_20250913\250913_E8_VTK'))
    pub = SimpleMqttPublisher()
    pub.connect(username='master', password='master')

    for _ in range(100):
        for string in str_list:
            pub.publish(PINTEL_TOPIC_SIM, string)
            # result.wait_for_publish()
            time.sleep(0.5)
        time.sleep(10)

    pub.disconnect()
