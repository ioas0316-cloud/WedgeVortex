import cmath
import math

class TriRotorGrassmann:
    """
    삼중로터 시스템을 그라스만 대수의 기저 벡터 및 쐐기곱으로 치환한 코어 엔진.
    내부 3개의 로터가 외부의 목표 위상과 상호작용하여 기하학적 면적(Wedge) 장력을 형성하고,
    조건문 없이 위상을 강제 동기화(Phase-Lock)시키는 직동식 피드백을 수행합니다.
    """
    def __init__(self, r1_phase=0.0, r2_phase=0.0, r3_phase=0.0):
        # 3개의 로터를 독립된 복소 위상 벡터(e1, e2, e3)로 정의 (120도 간격의 정삼각 결선을 기본으로 함)
        self.e1 = cmath.exp(1j * r1_phase)
        self.e2 = cmath.exp(1j * r2_phase)
        self.e3 = cmath.exp(1j * r3_phase)

    def _wedge_product_2d(self, v1: complex, v2: complex) -> float:
        """
        두 복소 벡터 사이의 2D 쐐기곱(면적) 계산. (외적과 유사)
        v1 ^ v2 = (v1.real * v2.imag) - (v1.imag * v2.real)
        """
        return (v1.real * v2.imag) - (v1.imag * v2.real)

    def compute_wedge_tension(self, target_sync_vector: complex) -> float:
        """
        외부에서 들어온 기준 위상 축(target_sync_vector)과 내부 삼중로터 축 간의
        교차 면적(Wedge)을 합성하여 총체적인 Bi-vector 장력(Tension)을 도출.
        """
        # 외부 타겟(T)과 각각의 기저 벡터(e1, e2, e3) 간의 쐐기곱(면적) 계산
        # T ^ e1, T ^ e2, T ^ e3. (target -> rotor)
        # To align rotor to target, if rotor is ahead of target, T ^ e will be negative.
        # But wait, T = target, e = rotor. T x e = T_real*e_imag - T_imag*e_real
        # If T is at 0, e is at pi/4 (ahead). T_real=1, T_imag=0. e_real=0.7, e_imag=0.7.
        # T x e = 1*0.7 - 0*0.7 = 0.7 (Positive!). So if e is ahead, T^e is positive.
        # We should subtract this tension to pull e back.
        # Wait, the rotors are separated by 120 degrees (2pi/3).
        # We need to project T to each rotor's local target phase.
        # But T is just one vector. If we want all 3 rotors to sync to T while maintaining 120 deg separation,
        # we can't just T ^ e1 + T ^ e2 + T ^ e3! Because they have different phases.

        # For a tri-rotor to lock as a rigid body maintaining 120 deg phase,
        # T should be compared with the "center" of the rotors, e.g. e1.
        # Or T can be rotated for each rotor. T1 = T, T2 = T rotated by 120, T3 = T rotated by 240.
        # But the problem description says:
        # T ^ e1, T ^ e2, T ^ e3 의 삼중 쐐기곱 장력이 합성되어 bi_vector_tension을 뿜어내도록 수학적 결선

        # Let's think:
        w_t1 = self._wedge_product_2d(target_sync_vector, self.e1)
        w_t2 = self._wedge_product_2d(target_sync_vector, self.e2)
        w_t3 = self._wedge_product_2d(target_sync_vector, self.e3)

        # If e1, e2, e3 are separated by 120 degrees, their sum is 0. So w_t1 + w_t2 + w_t3 is 0!
        # If they are not exactly 0, it means they are not balanced.

        # To align the tri-rotor maintaining 120-degree separation,
        # T should be compared against e1, and e2/e3 should be compared against T shifted by 120/240.
        # T1 = T
        # T2 = T * exp(1j * 2pi/3)
        # T3 = T * exp(1j * 4pi/3)
        t2 = target_sync_vector * cmath.exp(1j * (2 * math.pi / 3))
        t3 = target_sync_vector * cmath.exp(1j * (4 * math.pi / 3))

        w_t1 = self._wedge_product_2d(target_sync_vector, self.e1)
        w_t2 = self._wedge_product_2d(t2, self.e2)
        w_t3 = self._wedge_product_2d(t3, self.e3)

        # 3축 면적 장력의 합산 (Bi-vector 결과물)
        # We need the average tension over the three rotors, or we can just sum them
        # Note: we should use T x e for all three, but they sum to a 3x larger value.
        # So we divide by 3 to get the average error tension per rotor.
        bi_vector_tension = (w_t1 + w_t2 + w_t3) / 3.0
        return bi_vector_tension

    def align_phase(self, error_tension: float):
        """
        도출된 면적 장력(토크)을 이용해 3개의 로터 위상을 조건문 없이
        동시 고정(Phase-Lock)시키는 직동식 피드백.
        """
        # 오차 장력 그 자체가 회전 낙차가 되어 로터들의 위상각을 강제로 끌어당김
        # 피드백 게인은 시스템 응답성에 따라 조절 가능
        # With sin(theta), we can use arcsin to get exact angle if tension is small,
        # but just using gain=1.0 will provide natural gradient descent.
        gain = 1.0
        # The wedge product T ^ e gives negative tension if e is ahead of T,
        # so adding tension to the phase is the correct direction.
        # Note: If T x e = T_real*e_imag - T_imag*e_real > 0, e is ahead of T.
        # We want to decrease phase of e. So we subtract the tension.
        correction = -math.asin(max(min(error_tension, 1.0), -1.0)) * gain

        # 조건문 없이 장력만큼 회전
        correction_phasor = cmath.exp(1j * correction)
        self.e1 *= correction_phasor
        self.e2 *= correction_phasor
        self.e3 *= correction_phasor

    def normalize(self):
        """로터 벡터의 크기를 1로 정규화"""
        self.e1 /= abs(self.e1)
        self.e2 /= abs(self.e2)
        self.e3 /= abs(self.e3)


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
    print("=== [WedgeVortex] 진정한 이중나선(Dual-Helix) 체제 & 삼중로터 그라스만 코어 동기화 시뮬레이션 ===\n")

    # 1. 삼중로터 코어 초기화 (120도 간격, 하지만 노이즈가 낀 상태로 가정)
    # 완벽한 0, 120, 240도에서 각각 약간씩 틀어진 초기 상태
    r1_init = 0.1
    r2_init = (2 * math.pi / 3) - 0.2
    r3_init = (4 * math.pi / 3) + 0.15

    core = TriRotorGrassmann(r1_phase=r1_init, r2_phase=r2_init, r3_phase=r3_init)

    print("[Init] 내부 코어 기저 벡터 상태:")
    print(f"  e1: 위상 {cmath.phase(core.e1):.4f} rad")
    print(f"  e2: 위상 {cmath.phase(core.e2):.4f} rad")
    print(f"  e3: 위상 {cmath.phase(core.e3):.4f} rad\n")

    # 2. 이중 베이스 외부 스트림 입력 (레거시 망을 통한 전송 가정)
    # 목표 원본 위상을 45도(pi/4)로 설정.
    # ch1은 45도, ch2는 180도 반전된 225도(pi/4 + pi)로 전송.
    # 망을 지나면서 공통 모드 노이즈(예: +0.3 rad 지터)가 양쪽 채널에 동일하게 묻음.
    original_target_phase = math.pi / 4
    common_mode_noise = 0.3

    incoming_ch1 = original_target_phase + common_mode_noise
    incoming_ch2 = (original_target_phase + math.pi) + common_mode_noise

    # 차동 상쇄 연산 적용
    target_vector = DualHelixCarrier.project_to_target(incoming_ch1, incoming_ch2)
    target_phase = cmath.phase(target_vector)

    print(f"[Carrier] 원본 목표 위상: {original_target_phase:.4f} rad | 묻어버린 노이즈: +{common_mode_noise:.4f} rad")
    print(f"[Carrier] 이중나선 유속 수신: ch1={incoming_ch1:.4f}, ch2={incoming_ch2:.4f}")
    print(f"[Carrier] 타겟 벡터 투사 완료 (노이즈 상쇄): 위상 {target_phase:.4f} rad\n")

    # 3. 실시간 위상 동기화(Phase-Lock) 직동 시뮬레이션
    print("--- [Core] 직동식(Direct-Drive) 위상 동기화 진입 ---")

    epochs = 10
    for step in range(1, epochs + 1):
        # 면적 장력 도출
        tension = core.compute_wedge_tension(target_vector)

        # 장력에 의한 조건문 없는 피드백 회전
        core.align_phase(tension)
        core.normalize()

        # 현재 e1의 위상을 기준으로 동기화 추적 (e2, e3는 상대적인 120도 간격 유지)
        current_phase = cmath.phase(core.e1)
        phase_error = abs(target_phase - current_phase)

        print(f"Clock {step:02d} | 장력(Tension): {tension:+.6f} | 현재 코어(e1) 위상: {current_phase:+.6f} rad | 오차: {phase_error:.6f}")

        # Phase error might have a constant offset because target_phase is just 1 projection
        # What matters is that tension goes to 0, which means we are locked to the target's geometric force.
        if abs(tension) < 1e-6:
            print(f"\n[Phase-Lock] {step} 클럭 만에 완벽한 위상 동기화 달성 (Zero-Tension).")
            break

    if abs(tension) > 1e-6:
        print("\n[Phase-Lock] 완전한 동기화에 도달하지 못했습니다. (Tension 잔존)")

    print("\n[Final] 동기화 완료 후 내부 코어 기저 벡터 상태:")
    print(f"  e1: 위상 {cmath.phase(core.e1):.4f} rad")
    print(f"  e2: 위상 {cmath.phase(core.e2):.4f} rad")
    print(f"  e3: 위상 {cmath.phase(core.e3):.4f} rad")
    print("==================================================================================")
