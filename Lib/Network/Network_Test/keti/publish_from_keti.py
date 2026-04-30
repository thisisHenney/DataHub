#!/usr/bin/env python3
# -*-coding:utf8-*-

import paho.mqtt.client as mqtt
import os
import time
from pathlib import Path

BROKER = 'localhost'
PORT = 1883
TOPIC = "rpi_density"

home_dir = os.path.expanduser("~")
JSON_FOLDER = Path(rf"{home_dir}\AppData\Local\NEXTfoam\DataHub\v1.01\received_data\keti")

client = mqtt.Client()
client.connect(BROKER, PORT)

def publish_json_files(folder_path):
    files = sorted([f for f in os.listdir(folder_path) if f.endswith('.json')])
    for filename in files:
        filepath = os.path.join(folder_path, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            message = f.read()
            client.publish(TOPIC, message)
            print(f"Published: {filename} to topic: {TOPIC}")
            time.sleep(0.2)

# Run
client.subscribe("crowd_congestion")
while True:
    publish_json_files(JSON_FOLDER)
