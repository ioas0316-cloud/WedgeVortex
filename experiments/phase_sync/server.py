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

# The Server is dead. It is now merely a dumb fabric (Router/Relay)
# that allows decentralized nodes to discover each other's Phase States.
clients = set()

async def handler(websocket):
    """
    Acts solely as a relay for decentralized gossip. No physics occur here.
    """
    clients.add(websocket)
    try:
        async for message in websocket:
            # When a node broadcasts its localized state, relay it to peers.
            # In a true massive mesh, this would only route to K-nearest neighbors.
            # For this experiment, we form a complete graph mesh.
            other_clients = clients - {websocket}
            if other_clients:
                await asyncio.gather(*(c.send(message) for c in other_clients), return_exceptions=True)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)
        # Notify remaining peers that a node vanished so they can restructure
        if clients:
            disconnect_msg = json.dumps({"type": "node_disconnected"})
            await asyncio.gather(*(c.send(disconnect_msg) for c in clients), return_exceptions=True)

def start_http_server():
    web_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(web_dir)
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", HTTP_PORT), Handler) as httpd:
        print(f"Observatory UI at http://{WS_HOST}:{HTTP_PORT}")
        httpd.serve_forever()

async def main():
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    print(f"Decentralized Relay starting on ws://{WS_HOST}:{WS_PORT}")
    async with websockets.serve(handler, WS_HOST, WS_PORT):
        # We just sleep forever. The server does no work.
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
