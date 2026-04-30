import asyncio
import time
from datetime import datetime
from pathlib import Path

import websockets
import json
import os

# 순환할 JSON 파일들이 들어있는 폴더
FOLDER = Path("./example_json/vueron_02")
PORT = 65000


async def send_json(websocket):
    files = FOLDER.glob('*.json')
    sorted_files = sorted(files, key=lambda x: int(x.stem.split('_')[-1]))

    gap_and_file_list: list[tuple[int, Path]] = []
    last_time = 0
    for f in sorted_files:
        t = int(f.stem.split('_')[-1])
        if last_time == 0:
            last_time = t
            gap_and_file_list.append((0, f))
        else:
            gap = t - last_time
            last_time = t
            gap_and_file_list.append((gap, f))

    for gap, f in gap_and_file_list:
        await asyncio.sleep(gap/1000)
        with open(f, "r", encoding="utf-8") as fj:
            message = json.load(fj)
            now = datetime.utcnow()
            message['trID'] = now.strftime('%Y%m%d%H%M%S%f')
        await websocket.send(json.dumps(message, ensure_ascii=False))
        print(f"Sent {f.stem}")


async def main():
    async with websockets.serve(send_json, "localhost", PORT):
        print(f"WebSocket server running on ws://localhost:{PORT}")
        await asyncio.Future()  # 서버가 계속 실행되도록 블록


if __name__ == "__main__":
    asyncio.run(main())

