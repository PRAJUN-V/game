import json
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Dict, List
from game_logic import LudoGame
from database import save_game, load_game

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/create")
async def create_room(player_name: str = Form(...)):
    room_id = str(uuid.uuid4())[:8]
    game = LudoGame(room_id)
    game.add_player(player_name)
    save_game(room_id, game)
    return RedirectResponse(url=f"/room/{room_id}?player_name={player_name}", status_code=303)

@app.post("/join")
async def join_room(room_id: str = Form(...), player_name: str = Form(...)):
    game = load_game(room_id)
    if game:
        if game.add_player(player_name):
            save_game(room_id, game)
            return RedirectResponse(url=f"/room/{room_id}?player_name={player_name}", status_code=303)
        return HTMLResponse(content="Room full or game started", status_code=400)
    return HTMLResponse(content="Room not found", status_code=404)

@app.get("/room/{room_id}", response_class=HTMLResponse)
async def get_room(request: Request, room_id: str, player_name: str):
    game = load_game(room_id)
    if not game:
        return RedirectResponse(url="/")
    
    color = "spectator"
    for p in game.players:
        if p.name == player_name:
            color = p.color
            break

    return templates.TemplateResponse(request=request, name="room.html", context={
        "room_id": room_id, 
        "player_name": player_name,
        "color": color
    })

@app.websocket("/ws/{room_id}/{player_name}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_name: str):
    await manager.connect(room_id, websocket)
    game = load_game(room_id)
    
    if not game:
        await websocket.close()
        return

    # Broadcast initial state
    await manager.broadcast(room_id, {"type": "update", "state": game.get_state()})

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Re-load game to get freshest state from DB
            game = load_game(room_id)
            if not game: break
            
            # Only current player can act
            if game.current_player.name == player_name:
                if message["action"] == "roll":
                    game.roll_dice()
                elif message["action"] == "move":
                    game.move_piece(message["piece_id"])
                elif message["action"] == "start":
                    game.start_game()
                
                save_game(room_id, game)
                await manager.broadcast(room_id, {"type": "update", "state": game.get_state()})
            else:
                await websocket.send_json({"type": "error", "message": "Not your turn"})

    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
