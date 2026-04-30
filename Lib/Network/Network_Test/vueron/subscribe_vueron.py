import asyncio
import websockets

# 접속할 웹소켓 주소
WS_URL = "ws://localhost:65000/ws/v1/2"

async def hello():
    # 서버에 접속
    async with websockets.connect(WS_URL) as websocket:
        # 예시로 서버에 메시지 보내기
        await websocket.send("hello")
        print("서버에 메시지 전송: hello")
        
        # 서버로부터 응답 받기 (예시)
        try:
            response = await websocket.recv()
            print(f"서버 응답: {response}")
        except websockets.ConnectionClosed:
            print("연결이 종료되었습니다.")

if __name__ == "__main__":
    asyncio.run(hello())

