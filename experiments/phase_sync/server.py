import asyncio
import websockets
import json
import math
import time
import http.server
import socketserver
import threading
import os

# --- Configuration ---
WS_HOST = "0.0.0.0"
WS_PORT = 8765
HTTP_PORT = 8000

# --- Physics Constants ---
# The physics must match the client exactly.
# This proves the "shared coherence" - both sides calculate the same physics.
ATTRACTION_K = 0.05
REPULSION_K = 0.1
REPULSION_DIST = math.pi * (2/3) # 120 degrees in radians
MASTER_SPEED = 0.05 # Speed of the master time rotor

class CoherenceEngine:
    def __init__(self):
        # The Master Rotor (Absolute Time/Space Reference)
        self.master_phase = 0.0

        # 3 Data Rotors, initially at 0, 0, 0
        # They will naturally seek 120 deg separation via physics.
        self.phases = [0.0, 0.0, 0.0]

    def step_physics(self):
        """
        Advances the physics engine by one tick.
        Calculates attraction to the center (neutral point) and repulsion between rotors.
        """
        self.master_phase = (self.master_phase + MASTER_SPEED) % (2 * math.pi)

        # Calculate Delta-Wye Center (Neutral Point / Ground)
        # We calculate the vector sum to find the "center of mass" of the phases.
        sum_x = sum(math.cos(p) for p in self.phases)
        sum_y = sum(math.sin(p) for p in self.phases)
        center_phase = math.atan2(sum_y, sum_x)

        new_phases = list(self.phases)

        for i in range(3):
            # 1. Attraction: Pull towards the neutral point (center_phase)
            # But actually we want them to balance around it.
            # To achieve 120 deg spread naturally, they should repel each other,
            # and potentially track the master phase as a reference frame.

            # Repulsion from other rotors
            repulsion_force = 0.0
            for j in range(3):
                if i == j:
                    continue
                # Calculate shortest angular distance
                diff = self.phases[i] - self.phases[j]
                # Normalize to [-pi, pi]
                diff = (diff + math.pi) % (2 * math.pi) - math.pi

                # If they are closer than 120 degrees, push apart.
                # If they are perfectly 120 apart, force is 0.
                if abs(diff) < REPULSION_DIST:
                    # Sign determines direction to push
                    direction = 1 if diff > 0 else -1
                    magnitude = (REPULSION_DIST - abs(diff)) * REPULSION_K
                    repulsion_force += direction * magnitude

            # 2. Master tracking: Rotors follow the master time phase overall.
            # This makes the whole system rotate together.
            # We add the master speed to their phase.

            new_phases[i] = (self.phases[i] + MASTER_SPEED + repulsion_force) % (2 * math.pi)

        self.phases = new_phases

    def apply_distortion(self, rotor_index, delta_phase):
        """
        Applies a sudden spatiotemporal distortion (from user touch) to a rotor.
        """
        self.phases[rotor_index] = (self.phases[rotor_index] + delta_phase) % (2 * math.pi)


# Shared engine instance
engine = CoherenceEngine()
clients = set()

async def sync_loop():
    """
    The heartbeat of the server. Steps the physics and broadcasts the absolute master phase.
    """
    while True:
        engine.step_physics()

        # Broadcast only the Master Phase and perhaps the current local state
        # to show the local server's view of the universe.
        if clients:
            message = json.dumps({
                "type": "sync",
                "master_phase": engine.master_phase,
                "server_phases": engine.phases
            })
            # Send to all connected clients
            await asyncio.gather(*(client.send(message) for client in clients), return_exceptions=True)

        await asyncio.sleep(1/60) # Sync tick rate with requestAnimationFrame (60 FPS)

async def handler(websocket, path):
    """
    Handles incoming WebSocket connections and listens for Distortions (Deltas).
    """
    clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "distortion":
                rotor_idx = data["rotor"]
                delta = data["delta"]
                print(f"Distortion received: Rotor {rotor_idx} shifted by {delta:.2f} rad")
                engine.apply_distortion(rotor_idx, delta)

                # Echo the distortion to OTHER clients if there are multiple,
                # so they all experience the same spatial distortion simultaneously.
                distortion_msg = json.dumps({
                    "type": "distortion",
                    "rotor": rotor_idx,
                    "delta": delta
                })
                other_clients = clients - {websocket}
                if other_clients:
                     await asyncio.gather(*(c.send(distortion_msg) for c in other_clients), return_exceptions=True)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)

def start_http_server():
    """
    Starts a simple HTTP server to serve index.html.
    """
    web_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(web_dir)
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", HTTP_PORT), Handler) as httpd:
        print(f"Serving UI at http://{WS_HOST}:{HTTP_PORT}")
        httpd.serve_forever()

async def main():
    # Start HTTP server in a background thread
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    # Start WebSocket server
    print(f"WebSocket server starting on ws://{WS_HOST}:{WS_PORT}")
    async with websockets.serve(handler, WS_HOST, WS_PORT):
        # Start the physics sync loop
        await sync_loop()

if __name__ == "__main__":
    asyncio.run(main())
