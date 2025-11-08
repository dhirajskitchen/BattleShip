from flask import Flask
from flask_socketio import SocketIO, emit
import random, threading, time
import ssl

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory mock game state
game_state = {
    "status": "in_progress",
    "my_board": [[0 for _ in range(10)] for _ in range(10)],
    "opponent_board": [[0 for _ in range(10)] for _ in range(10)],
    "is_my_turn": True,
    "status_message": "Your turn! Fire at will.",
    "opponent_name": "EnemyBot",
    "my_ships_health": {
        "Carrier": 5,
        "Battleship": 4,
        "Cruiser": 3,
        "Submarine": 3,
        "Destroyer": 2
    }
}


@app.route('/')
def index():
    return "Battleship Server is running!"


@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit('server_message', {'type': 'info', 'text': 'Connected to Battleship server'})
    emit('game_update', game_state)


@socketio.on('create_game')
def handle_create_game(data):
    player_name = data.get('player_name', 'Unknown')
    print(f"{player_name} created a game.")
    emit('server_message', {'type': 'success', 'text': f"Game created by {player_name}. Room ID: TEST123"})
    emit('game_update', game_state)


@socketio.on('join_game')
def handle_join_game(data):
    room_id = data.get('room_id', 'N/A')
    player_name = data.get('player_name', 'Unknown')
    print(f"{player_name} joined room {room_id}")
    emit('server_message', {'type': 'success', 'text': f"{player_name} joined room {room_id}."})
    emit('game_update', game_state)


@socketio.on('place_ships')
def handle_place_ships(data):
    print("Received ship placements:", data)
    emit('server_message', {'type': 'info', 'text': 'Ships placed!'})
    emit('game_update', game_state)


@socketio.on('make_shot')
def handle_make_shot(data):
    """Simulate firing at the opponent board with alternating turns."""
    r, c = data.get('r'), data.get('c')
    print(f"Player shot at ({r}, {c})")

    if not game_state["is_my_turn"]:
        emit('server_message', {'type': 'error', 'text': "Not your turn yet!"})
        return

    # Simulate hit or miss
    result = random.choice(['hit', 'miss'])
    game_state["opponent_board"][r][c] = 2 if result == 'hit' else 3
    game_state["is_my_turn"] = False
    game_state["status_message"] = f"You {result} at ({r}, {c}). Waiting for opponent..."

    emit('game_update', game_state, broadcast=True)

    # Simulate opponent move after delay, then give turn back
    def opponent_turn():
        time.sleep(2)
        rr, cc = random.randint(0, 9), random.randint(0, 9)
        game_state["my_board"][rr][cc] = random.choice([2, 3])
        game_state["is_my_turn"] = True
        game_state["status_message"] = f"Opponent fired at ({rr}, {cc}). Your turn!"
        socketio.emit('game_update', game_state)

    threading.Thread(target=opponent_turn, daemon=True).start()


if __name__ == '__main__':
    # SSL context for WSS support
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
    socketio.run(app, host='0.0.0.0', port=5005, debug=True, use_reloader=False, ssl_context=ssl_context)
