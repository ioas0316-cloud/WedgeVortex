import sys
import os

from lib.phase_inverter import PhaseInverterGate

gate = PhaseInverterGate()
print(gate.process_hybrid_causality_vortex({"payload": b'A'*128, "virtual_address_ptr": 10}))
