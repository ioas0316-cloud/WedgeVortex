import cmath
import math

class PhaseVector:
    """
    Represents a phase vector in the complex plane for the WedgeVortex architecture.
    """
    def __init__(self, magnitude: float, phase_angle: float):
        self.magnitude = magnitude
        self.phase_angle = phase_angle % (2 * math.pi)

    @property
    def complex_val(self):
        return cmath.rect(self.magnitude, self.phase_angle)

    def __xor__(self, other):
        """
        Overloads the ^ operator to represent the Grassmann Wedge Product.
        Calculates the Bi-vector area (voltage) between two phase vectors.
        A ^ B = |A| * |B| * sin(theta_A - theta_B)
        """
        if not isinstance(other, PhaseVector):
            raise TypeError("Wedge product is only defined between PhaseVectors.")

        # Calculate the directed area (wedge product)
        # Using the cross product analogue in 2D: A_x * B_y - A_y * B_x
        # which is equivalent to |A| * |B| * sin(angle_B - angle_A)
        # Here we define A ^ B as area = |A||B|sin(theta_A - theta_B)
        phase_diff = self.phase_angle - other.phase_angle
        area = self.magnitude * other.magnitude * math.sin(phase_diff)
        return area

    def __repr__(self):
        return f"PhaseVector(mag={self.magnitude:.2f}, phase={self.phase_angle:.2f} rad)"


class TriRotorSimulator:
    """
    Core engine for the Variable Tri-Rotor System.
    Handles self-healing synchronization based on the Wedge Product torque.
    """
    def __init__(self, initial_phase: float = 0.0):
        # The receiver's internal rotor phase
        self.rotor_vector = PhaseVector(magnitude=1.0, phase_angle=initial_phase)

    def sync_receive(self, incoming_vector: PhaseVector):
        """
        Direct-drive connection.
        Calculates A ^ B. If non-zero, applies torque to self-heal the phase.
        """
        # A = incoming wave (transmitted)
        # B = internal rotor wave (receiver)
        # Calculate Wedge Product (Area Voltage)
        bivector_area = incoming_vector ^ self.rotor_vector

        print(f"[Sync] Incoming: {incoming_vector}, Internal: {self.rotor_vector}")
        print(f"[Sync] Bivector Area (A ^ B): {bivector_area:.4f}")

        # Self-healing logic
        if abs(bivector_area) > 1e-9:
            # The non-zero area acts as a physical torque that pushes the rotor
            # to match the incoming phase instantly (simulated by updating phase)
            print(f"[Self-Healing] Torque applied! Adjusting phase by area {bivector_area:.4f}")
            # For this simulation, the torque instantly aligns the rotor to the incoming vector.
            # In a real physical system, the torque would naturally force the alignment.
            self.rotor_vector.phase_angle = incoming_vector.phase_angle
            print(f"[Self-Healing] Phase aligned. New Internal: {self.rotor_vector}")
        else:
            print("[Sync] Perfect synchronization. A ^ B = 0. Data bypassed.")

        return self.rotor_vector


class WedgeVortexNetworkMock:
    """
    Mock class for bypassing legacy UDP/IP networks.
    """
    @staticmethod
    def udp_encapsulate(vector: PhaseVector) -> dict:
        """
        Encapsulates the phase vector into a dummy UDP packet.
        """
        print(f"[Network] Encapsulating {vector} into UDP packet...")
        return {
            "src_port": 12345,
            "dst_port": 54321,
            "payload": {
                "mag": vector.magnitude,
                "phase": vector.phase_angle
            },
            "checksum": "dummy_hash"
        }

    @staticmethod
    def udp_decapsulate(packet: dict) -> PhaseVector:
        """
        Smashes the UDP header and extracts the raw phase flow.
        """
        print(f"[Network] Smashing UDP packet. Extracting phase payload...")
        payload = packet["payload"]
        return PhaseVector(magnitude=payload["mag"], phase_angle=payload["phase"])


# Example Usage (Can be run to demonstrate the mechanism)
if __name__ == "__main__":
    print("=== [WedgeVortex] Architecture Simulation ===\n")

    # 1. Initialization
    transmitter_wave = PhaseVector(1.0, math.pi / 4) # 45 degrees
    receiver = TriRotorSimulator(initial_phase=0.0)  # 0 degrees, out of sync

    # 2. Transmission through legacy network (UDP Mock)
    udp_packet = WedgeVortexNetworkMock.udp_encapsulate(transmitter_wave)

    # ... jitter or noise could happen here in reality ...

    # 3. Reception and Decapsulation
    incoming_wave = WedgeVortexNetworkMock.udp_decapsulate(udp_packet)

    # 4. Direct-drive Sync & Self-healing
    print("\n--- Direct-Drive Synchronization ---")
    receiver.sync_receive(incoming_wave)

    # 5. Subsequent transmission (Perfect sync state)
    print("\n--- Next Packet (Already Synced) ---")
    next_wave = PhaseVector(1.0, math.pi / 4)
    receiver.sync_receive(next_wave)
