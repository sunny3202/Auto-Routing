"""
algorithm_utility.py — AlgorithmUtility 클래스

경로 단순화 유틸리티. SmartRoutingAI의 AlgorithmUtility를 대체.
RuleSet postprocessing.py가 직접 호출한다.
"""

import numpy as np


class AlgorithmUtility:
    """
    경로 후처리 유틸리티.
    두 메서드 모두 in-place 수정 후 같은 리스트를 반환한다.
    """

    @staticmethod
    def delete_empty_line(path_np: list[np.ndarray]) -> list[np.ndarray]:
        """
        중복 점 제거 (두 점 사이 거리가 임계값 이하이면 제거).
        in-place 수정.
        """
        THRESHOLD = 1e-3  # mm
        i = 1
        while i < len(path_np):
            if float(np.linalg.norm(path_np[i] - path_np[i - 1])) < THRESHOLD:
                path_np.pop(i)
            else:
                i += 1
        return path_np

    @staticmethod
    def get_path_simplification(path_np: list[np.ndarray]) -> list[np.ndarray]:
        """
        Collinear 점 제거: 세 점 A, B, C에서 AB × AC의 크기가 임계값 이하이면 B 제거.
        in-place 수정.
        """
        CROSS_THRESHOLD = 1e-6
        i = 1
        while i < len(path_np) - 1:
            a = path_np[i - 1]
            b = path_np[i]
            c = path_np[i + 1]
            ab = b - a
            ac = c - a
            cross = np.cross(ab, ac)
            if float(np.linalg.norm(cross)) < CROSS_THRESHOLD:
                path_np.pop(i)
            else:
                i += 1
        return path_np


class MathUtility:
    """SmartRoutingAI MathUtility 대체 (postprocessing.py 호환)"""

    @staticmethod
    def to_tuple(v: np.ndarray) -> tuple[float, float, float]:
        return (float(v[0]), float(v[1]), float(v[2]))
