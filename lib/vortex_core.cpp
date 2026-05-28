#include <cmath>
#include <stdint.h>
#include <cstring> // Required for std::memcpy

extern "C" {
    static float pinned_free_vram = 3.0f * 1024.0f * 1024.0f * 1024.0f;
    static float pinned_total_vram = 3.0f * 1024.0f * 1024.0f * 1024.0f;
    static const float inv_sqrt3 = 1.0f / std::sqrt(3.0f);

    void init_pinned_memory_pool(double vram_size) {
        pinned_total_vram = (float)vram_size;
        pinned_free_vram = (float)vram_size;
    }

    struct TrajectoryRotor {
        float past_momentum;
        float present_phase;
        float future_gravity;
    };

    static uint64_t previous_lattice_state = 0;

    int execute_causality_vortex(
        int raw_len,
        int survival_factor,
        int is_missing,
        uint32_t virtual_address_ptr,
        const char* raw_payload,
        float* past_momentum,
        float* future_gravity
    ) {
        // [1] Dynamic Pinned VRAM Territorial Shift
        pinned_free_vram -= (float)raw_len;
        if (pinned_free_vram <= 0.0f) {
            pinned_free_vram = pinned_total_vram;
        }

        // [2] O(1) Volumetric Lattice Sync & Hardware Latch
        float byte_wave_energy = 0.0f;
        uint64_t core_signature = 0;

        if (!is_missing && raw_payload != nullptr && raw_len >= 16) {
            // Master's Volumetric Sensing: Instead of sequential O(N) loop, latch the start, middle, and end in one tick
            // Using memcpy to prevent Undefined Behavior (unaligned memory access) and ensure OOB safety
            const uint8_t* mem_ptr = reinterpret_cast<const uint8_t*>(raw_payload);
            uint64_t start_latch = 0, mid_latch = 0, end_latch = 0;

            // Note: Since raw_len >= 16, raw_len/2 is at least 8. Thus mid_latch reads bytes 8..15, which is safely within raw_len bounds.
            std::memcpy(&start_latch, mem_ptr, sizeof(uint64_t));
            std::memcpy(&mid_latch, mem_ptr + (raw_len / 2), sizeof(uint64_t));
            std::memcpy(&end_latch, mem_ptr + raw_len - sizeof(uint64_t), sizeof(uint64_t));

            core_signature = start_latch ^ mid_latch ^ end_latch;
        }

        float phase_angle = 0.0f;
        if (core_signature == previous_lattice_state) {
            phase_angle = 0.0f; // Phase is locked
        } else {
            phase_angle = static_cast<float>(core_signature % 360) * (3.141592f / 180.0f);
            previous_lattice_state = core_signature;
        }

        // Use phase angle and signature to calculate raw physical torque
        byte_wave_energy = static_cast<float>(core_signature % 1000) * std::cos(phase_angle);

        // Use byte_wave_energy as primary torque influence instead of just address ptr if available
        float structural_mass = byte_wave_energy != 0 ? byte_wave_energy : static_cast<float>(virtual_address_ptr & 0xFFFFFFFF);

        // Citizenship Bypass Filter: If phase is severely misaligned and not naturally resonant (noise), drop it by zeroing mass
        if (!is_missing && raw_payload != nullptr) {
             if (std::abs(phase_angle) > 3.0f && (virtual_address_ptr % 2 != 0)) {
                 return 0; // Centrifugal force expels the noise packet
             }
        }

        // [3] Holographic Phase-Lock Resonance & Causal Reconstruction
        int restored_mass = 0;
        if (is_missing) {
            float resonance_torque = (past_momentum[0] * past_momentum[0]) + (future_gravity[0] * future_gravity[0]);
            float restoration_force = std::sin(resonance_torque) * inv_sqrt3;

            restored_mass = (int)(resonance_torque * 300.0f);
            if (restored_mass <= 0) restored_mass = 256;
        }

        int final_mass = raw_len + restored_mass;

        float pressure = (float)final_mass / (pinned_free_vram + 1.0f);
        float orbit_angle = structural_mass * pressure;

        // [4] Trajectory Hologram Output
        TrajectoryRotor rotor;
        rotor.past_momentum   = std::cos(orbit_angle) * inv_sqrt3;
        rotor.present_phase  = std::sin(orbit_angle) * rotor.past_momentum;
        rotor.future_gravity = orbit_angle * rotor.present_phase;

        past_momentum[0] = rotor.past_momentum;
        future_gravity[0] = rotor.future_gravity;

        if (!survival_factor) {
            return 0; // Destroy noise natively
        }

        return is_missing ? restored_mass : raw_len;
    }
}
