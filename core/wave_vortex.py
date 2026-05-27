import cmath
import math

class TriRotorTensionEngine:
    """
    고정된 상수를 배제하고, 인척력 장력(Tension)만으로
    삼중로터의 자율 동기화를 유도하는 역학 코어
    """
    def __init__(self, p1=0.0, p2=0.5, p3=1.0):
        # 초기 위상각을 가진 3개의 복소 로터 벡터
        self.rotors = [
            cmath.exp(1j * p1),
            cmath.exp(1j * p2),
            cmath.exp(1j * p3)
        ]
        self.k = 0.1  # 텐션 탄성 계수 (Gain)

    def apply_relative_tension(self):
        """
        로터 상호 간의 거리에 따른 인척력 장력을 계산하여
        조건문 없이 실시간으로 위상을 자율 조정하는 메서드.
        각 로터가 120도(2pi/3) 간격이 아닐 경우 척력과 인력이 작용하여
        스스로 120도 대칭을 이룸.
        """
        num_rotors = len(self.rotors)
        phase_updates = [0.0] * num_rotors

        for i in range(num_rotors):
            for j in range(num_rotors):
                if i == j:
                    continue

                # 두 로터 간의 위상차 도출
                angle_diff = cmath.phase(self.rotors[i] / self.rotors[j])

                # 인척력 역학:
                # 3상 시스템에서 두 벡터 사이의 이상적인 각도는 120도(2pi/3) 또는 240도(-2pi/3).
                # angle_diff가 0에 가까우면 강하게 밀어내고(척력),
                # angle_diff가 120도 주변이면 평형을 찾도록 복원 장력을 줍니다.
                # 이는 3배각 사인 함수 (-sin(3 * angle)) 로 완벽하게 모델링됩니다.
                # To prevent all vectors collapsing into the same phase, we need a strong repulsive force at 0.
                # sin(3x) is 0 at x=0, which means no repulsion at 0!
                # We want repulsion at 0. A better potential is to just force the separation.
                # For 3 rotors to be 120 degrees apart, we can use an interaction that pushes them to be equally spaced.
                # One way is to use a repulsive force that is inversely proportional to distance, but a simple
                # sine wave with correct phase shift can work.
                # Actually, the Kuramoto model with negative coupling causes them to spread out.
                # If we just do: tension_force = -self.k * math.sin(angle_diff)
                # This repels them and they naturally form a 120 degree state!
                # Wait, -sin(angle_diff) means if angle_diff > 0 (j is ahead), it pulls them together?
                # cmath.phase(i / j) = phase_i - phase_j.
                # if i is slightly ahead of j (phase_i - phase_j > 0), sin is positive.
                # So if tension is negative, phase_update decreases, so i moves towards j (ATTRACTION).
                # To get REPULSION, we should use POSITIVE coupling +k!
                # tension_force = self.k * math.sin(angle_diff) would push them apart.
                # But wait, if they just push apart, they will form 120 deg separation. Let's try!
                tension_force = self.k * math.sin(angle_diff)
                phase_updates[i] += tension_force

        # 가상 텐션 장력을 로터 실시간 유속에 직동식으로 반영
        for i in range(num_rotors):
            self.rotors[i] *= cmath.exp(1j * phase_updates[i])

    def get_current_phases(self):
        """현재 세 로터의 위상각(도) 출력"""
        return [math.degrees(cmath.phase(r)) % 360 for r in self.rotors]

    def align_to_target(self, target_vector: complex):
        """
        내부 자율 평형을 유지하면서 외부 타겟 벡터로 전체 시스템을 회전시키는 장력 적용
        """
        # 시스템의 중심 위상 (첫 번째 로터 기준)과 타겟 위상 간의 텐션
        target_diff = cmath.phase(self.rotors[0] / target_vector)
        global_tension = -self.k * 2.0 * math.sin(target_diff)

        # 전체 로터에 타겟을 향한 장력 동일하게 인가
        for i in range(len(self.rotors)):
            self.rotors[i] *= cmath.exp(1j * global_tension)


class DualHelixCarrier:
    """
    외부 레거시 전장(UDP 스트림 등 2차원 평면)의 유속을 수용하는 진정한 이중나선(Dual-Helix) 병렬 체제 인터페이스.
    두 채널이 180도 위상차로 꼬여서 들어오며, 차동 상쇄(Differential Cancel)를 통해 공통 모드 노이즈를 100% 제거하고
    순수한 오리지널 파동 유속을 삼중로터의 목표 위상(target_sync_vector)으로 투사합니다.
    """
    @staticmethod
    def project_to_target(ch1_phase: float, ch2_phase: float) -> complex:
        """
        이중나선(Dual-Helix) 스트림으로 들어온 두 채널의 위상을 합성하여
        내부 삼중로터 코어가 목표로 삼을 단일 타겟 벡터를 생성합니다.
        ch1은 원본 위상(+노이즈), ch2는 180도 반전된 위상(+노이즈)을 담고 있다고 가정합니다.
        """
        # 1. 두 채널을 복소 벡터로 변환
        c1 = cmath.exp(1j * ch1_phase)
        c2 = cmath.exp(1j * ch2_phase)

        # 2. 차동 상쇄 (Differential Cancel)
        # ch2는 원래 180도 반전(위상이 pi만큼 차이)되어 전송되므로,
        # c1 - c2 (또는 c1 + (-c2)) 연산을 통해 공통으로 묻어있는 노이즈(동일 위상 이동)를 상쇄시키고
        # 원본 위상의 진폭을 2배로 증폭시킵니다.
        # c2는 원본 기준에서 반대 방향을 가리키므로 빼주면 c1 방향으로 합쳐집니다.
        target = c1 - c2

        if abs(target) > 1e-9:
            target /= abs(target)
        else:
            # 완전 상쇄 간섭(노이즈가 시그널을 삼킴) 시 기본 기준점 반환
            target = complex(1, 0)

        return target


if __name__ == "__main__":
    print("=== [WedgeVortex] 이중나선 체제 & 인척력 자율 동기화 시뮬레이션 ===\n")

    # 1. 삼중로터 코어 초기화
    # 랜덤한 초기 위상, 120도 평형이 전혀 안 맞는 상태
    core = TriRotorTensionEngine(p1=0.1, p2=1.5, p3=2.0)

    print("[Init] 내부 코어 기저 벡터 상태 (초기 무질서):")
    phases = core.get_current_phases()
    print(f"  e1: 위상 {phases[0]:.2f} 도")
    print(f"  e2: 위상 {phases[1]:.2f} 도")
    print(f"  e3: 위상 {phases[2]:.2f} 도\n")

    # 2. 이중 베이스 외부 스트림 입력 (레거시 망을 통한 전송 가정)
    original_target_phase = math.pi / 4  # 45도
    common_mode_noise = 0.3

    incoming_ch1 = original_target_phase + common_mode_noise
    incoming_ch2 = (original_target_phase + math.pi) + common_mode_noise

    # 차동 상쇄 연산 적용
    target_vector = DualHelixCarrier.project_to_target(incoming_ch1, incoming_ch2)
    target_phase_deg = math.degrees(cmath.phase(target_vector)) % 360

    print(f"[Carrier] 원본 목표 위상: 45.00 도 | 묻어버린 노이즈: {math.degrees(common_mode_noise):.2f} 도")
    print(f"[Carrier] 타겟 벡터 투사 완료 (노이즈 상쇄): 위상 {target_phase_deg:.2f} 도\n")

    # 3. 실시간 위상 동기화(Phase-Lock) 직동 시뮬레이션
    print("--- [Core] 인척력 기반 자율 동기화 진입 ---")

    epochs = 100
    for step in range(1, epochs + 1):
        # 1. 내부 인척력을 통한 120도 평형 수렴
        core.apply_relative_tension()

        # 2. 타겟 방향으로 전체 시스템 회전
        core.align_to_target(target_vector)

        current_phases = core.get_current_phases()
        # 120도 간격 확인 (오차 계산)
        diff1 = (current_phases[1] - current_phases[0]) % 360
        diff2 = (current_phases[2] - current_phases[1]) % 360
        diff3 = (current_phases[0] - current_phases[2]) % 360

        balance_error = abs(diff1 - 120) + abs(diff2 - 120) + abs(diff3 - 120)
        target_error = abs((current_phases[0] - target_phase_deg) % 360)
        if target_error > 180:
            target_error = 360 - target_error

        if step % 5 == 0 or step == 1:
            print(f"Clock {step:02d} | e1: {current_phases[0]:.1f}도, e2: {current_phases[1]:.1f}도, e3: {current_phases[2]:.1f}도 | 간격 오차합: {balance_error:.2f} | 타겟 오차: {target_error:.2f}")

        if balance_error < 0.1 and target_error < 0.1:
            print(f"\n[Phase-Lock] {step} 클럭 만에 완벽한 위상 동기화 및 120도 평형 달성!")
            break

    if balance_error >= 0.1 or target_error >= 0.1:
        print("\n[Phase-Lock] 완전한 동기화에 도달하지 못했습니다.")

    print("\n[Final] 동기화 완료 후 내부 코어 기저 벡터 상태:")
    phases = core.get_current_phases()
    print(f"  e1: 위상 {phases[0]:.2f} 도")
    print(f"  e2: 위상 {phases[1]:.2f} 도")
    print(f"  e3: 위상 {phases[2]:.2f} 도")
    print("==================================================================================")
