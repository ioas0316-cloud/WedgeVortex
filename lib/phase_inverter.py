import sys
import os
import ctypes
from typing import Dict, Tuple

class MockHardwareBridge:
    def get_realtime_vram_state(self) -> Tuple[int, int]:
        return (3 * 1024 * 1024 * 1024, 3 * 1024 * 1024 * 1024)

lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libvortex.so')

if not os.path.exists(lib_path):
    import subprocess
    print(f"[PhaseInverterGate] {lib_path} not found. Attempting to build...")
    subprocess.run(["make", "-C", os.path.dirname(lib_path)], check=True)

try:
    vortex_lib = ctypes.CDLL(lib_path)
    vortex_lib.init_pinned_memory_pool.argtypes = [ctypes.c_double]
    vortex_lib.init_pinned_memory_pool.restype = None
    vortex_lib.execute_causality_vortex.argtypes = [
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32, ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)
    ]
    vortex_lib.execute_causality_vortex.restype = ctypes.c_int
except OSError as e:
    raise RuntimeError(f"Failed to load C++ core at {lib_path}. Please build it using `make` in `lib/` directory.") from e

class PhaseInverterGate:
    def __init__(self, hardware_bridge=None):
        self.hw_bridge = hardware_bridge if hardware_bridge else MockHardwareBridge()

        self._past_momentum = ctypes.c_float(1.0)
        self._past_momentum_ptr = ctypes.byref(self._past_momentum)

        self._future_gravity = ctypes.c_float(1.0)
        self._future_gravity_ptr = ctypes.byref(self._future_gravity)

        self.free_vram, _ = self.hw_bridge.get_realtime_vram_state()
        vortex_lib.init_pinned_memory_pool(float(self.free_vram))

        self._execute_causality_vortex = vortex_lib.execute_causality_vortex

    def process_hybrid_causality_vortex(self, packet_map_stream: Dict, noise_mask: int = 0, identity_filter: int = 0) -> bytes:
        current_bytes = packet_map_stream["payload"]
        raw_len = len(current_bytes)

        survival = (noise_mask ^ identity_filter) & 1
        missing = 1 if raw_len == 0 else 0
        address_ptr = packet_map_stream.get("virtual_address_ptr", 0)

        out_mass = self._execute_causality_vortex(
            raw_len,
            survival,
            missing,
            address_ptr,
            current_bytes if not missing else None,
            self._past_momentum_ptr,
            self._future_gravity_ptr
        )
        return b'\x00' * out_mass if out_mass > 0 else b''
