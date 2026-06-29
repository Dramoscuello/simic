from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    """
    Gestor de conexiones WebSocket para monitoreo de simulacros.
    Agrupa conexiones por institucion_id.
    """
    def __init__(self):
        # {institucion_id: [WebSocket]}
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, institucion_id: int):
        await websocket.accept()
        if institucion_id not in self.active_connections:
            self.active_connections[institucion_id] = []
        self.active_connections[institucion_id].append(websocket)
        print(f"🔌 WS: Nueva conexión en Institución {institucion_id}. Total: {len(self.active_connections[institucion_id])}")

    def disconnect(self, websocket: WebSocket, institucion_id: int):
        if institucion_id in self.active_connections:
            if websocket in self.active_connections[institucion_id]:
                self.active_connections[institucion_id].remove(websocket)
                if not self.active_connections[institucion_id]:
                    del self.active_connections[institucion_id]
            print(f"🔌 WS: Desconexión en Institución {institucion_id}")

    async def broadcast_to_institution(self, message: dict, institucion_id: int):
        """Envía un mensaje a todos los admins conectados de esa institución"""
        if institucion_id in self.active_connections:
            connections = self.active_connections[institucion_id]
            # Iterar copia para evitar problemas si se desconectan durante el loop
            for connection in connections[:]: 
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error enviando WS a inst {institucion_id}: {e}")
                    # Opcional: desconectar sockets muertos
                    # self.disconnect(connection, institucion_id)

manager = ConnectionManager()
