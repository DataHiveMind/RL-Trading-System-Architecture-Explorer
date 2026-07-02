from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Quant Dashboard API")

# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    """Manages active WebSocket connections to the dashboard."""
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for the React dashboard to receive live training/trading metrics.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and wait for messages from client (if any)
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from telemetry stream.")

# This function would be called by your trading loop to push data to the UI
async def push_telemetry(telemetry_data: dict):
    await manager.broadcast(telemetry_data)