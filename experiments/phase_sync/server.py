import asyncio
import websockets
import json
import os
import http.server
import socketserver
import threading

# --- Environment ---
WS_HOST = "0.0.0.0"
WS_PORT = 8765
HTTP_PORT = 8000

# The Server acts as a dumb fabric (Router/Relay)
# that allows decentralized nodes to discover each other's Phase States.
# It also provides a macro-view (Universe State) for the Galaxy Map.
clients = set()
# Track which channel each client is currently vibrating in
client_channels = {}

async def universe_pulse():
    """
    Periodically pulses the macro state of the universe (Galaxy Map)
    so nodes can see the clustering of Stars (Channels) without tracking individual physics.
    """
    while True:
        await asyncio.sleep(2.0) # Pulse every 2 seconds

        if not clients:
            continue

        # Aggregate universe state
        universe = {}
        for ch in client_channels.values():
            if ch not in universe:
                universe[ch] = 0
            universe[ch] += 1

        pulse_msg = json.dumps({
            "type": "universe_pulse",
            "galaxies": universe
        })

        await asyncio.gather(*(c.send(pulse_msg) for c in clients), return_exceptions=True)

async def handler(websocket):
    """
    Acts as a relay for decentralized gossip and tracking the macro universe.
    """
    clients.add(websocket)
    client_channels[websocket] = 0.0 # Default Global

    try:
        async for message in websocket:
            data = json.loads(message)

            # Track the client's current channel for the Galaxy Map
            if "channel" in data:
                client_channels[websocket] = data["channel"]

            # When a node broadcasts its localized state, relay it to peers.
            other_clients = clients - {websocket}
            if other_clients:
                await asyncio.gather(*(c.send(message) for c in other_clients), return_exceptions=True)
    except Exception:
        pass
    finally:
        clients.remove(websocket)
        if websocket in client_channels:
            del client_channels[websocket]

        # Notify remaining peers that a node vanished so they can restructure
        if clients:
            disconnect_msg = json.dumps({"type": "node_disconnected"})
            await asyncio.gather(*(c.send(disconnect_msg) for c in clients), return_exceptions=True)

def start_http_server():
    web_dir = os.path.dirname(os.path.abspath(__file__))
    # Create handler that explicitly serves from the given directory
    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=web_dir, **kwargs)

    with socketserver.TCPServer(("", HTTP_PORT), CustomHandler) as httpd:
        print(f"Observatory UI at http://{WS_HOST}:{HTTP_PORT}")
        httpd.serve_forever()

async def main():
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    print(f"Decentralized Relay starting on ws://{WS_HOST}:{WS_PORT}")
    async with websockets.serve(handler, WS_HOST, WS_PORT):
        # Start the slow macro-universe pulse
        await universe_pulse()

if __name__ == "__main__":
    asyncio.run(main())
