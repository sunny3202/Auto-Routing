"""
path_finder.py — PathFinder 클래스 (A* 기반)

A* 탐색 상태: (vx, vy, vz, dir_idx, turn_count, straight_count)
  dir_idx: 0~5 (축방향 6방향 인덱스)
  straight_count: 마지막 꺾임 이후 직선 이동 복셀 수 (min_straight_voxels 에서 캡)
    → straight_ok = (straight_count >= min_straight_voxels)
    → Phase 1: min_straight=150mm / voxel=300mm → min_straight_voxels=1 → 1복셀 충족

확정 파라미터: bending_weight, min_straight, turn_count_limit, timeout_sec
가설 파라미터: accuracy(snap distance로 구현)
대각 이동: Phase 1에서 축방향 6방향만 구현 (대각은 테스트 후 추가)
"""

import heapq
import math
import time
from typing import Optional

import numpy as np

from .voxel_grid import VoxelGrid

# 축방향 6방향 (dx, dy, dz)
_AXIS_DIRS: list[tuple[int, int, int]] = [
    (1, 0, 0), (-1, 0, 0),
    (0, 1, 0), (0, -1, 0),
    (0, 0, 1), (0, 0, -1),
]

# 방향 인덱스 매핑 (visited 집합 키로 사용)
_DIR_TO_IDX: dict[tuple[int, int, int], int] = {d: i for i, d in enumerate(_AXIS_DIRS)}
_NO_DIR_IDX = len(_AXIS_DIRS)  # 시작점 (방향 없음)


class PathFinder:
    """
    A* 기반 단일 경로 탐색기.
    RoutingPipeline이 entity별로 호출한다.
    """

    def find_path(
        self,
        start: tuple[float, float, float],
        end: tuple[float, float, float],
        grid: VoxelGrid,
        turn_count_limit: int,
        min_straight_distance: float,
        bending_optimization_weight: float,
        accuracy: float = 100.0,
        timeout_sec: float = 30.0,
    ) -> Optional[list[tuple[float, float, float]]]:
        """
        start, end: world 좌표 (mm)
        accuracy: 종료점 snap distance (가설 — 허용 오차 반경)
        timeout_sec: 탐색 시간 제한 (초과 시 None 반환)

        반환: world 좌표 리스트 (성공) 또는 None (실패/timeout)
        """
        vs = grid.voxel_size

        start_voxel = grid.world_to_voxel(start)
        end_voxel = grid.world_to_voxel(end)

        # 시작점 또는 종료점이 장애물이면 즉시 실패
        if grid.is_blocked(start_voxel):
            return None
        if grid.is_blocked(end_voxel):
            return None

        # accuracy를 복셀 단위로 변환 (종료 조건)
        accuracy_voxels = max(1, int(math.ceil(accuracy / vs)))

        # 허용 min_straight 복셀 수
        min_straight_voxels = int(math.ceil(min_straight_distance / vs)) if min_straight_distance > 0 else 0

        # ------------------------------------------------------------------
        # A* 오픈리스트: (f, g, state)
        # state = (vx, vy, vz, dir_idx, turn_count, straight_count)
        # straight_count: 마지막 꺾임 후 직선 이동 복셀 수 (min_straight_voxels 에서 캡)
        # 시작점: straight_count = min_straight_voxels (이미 충족 상태)
        # ------------------------------------------------------------------
        start_straight = min_straight_voxels  # 시작점에서는 제약 없음
        start_state = (start_voxel[0], start_voxel[1], start_voxel[2], _NO_DIR_IDX, 0, start_straight)
        h_start = self._heuristic(start_voxel, end_voxel, vs)
        open_heap: list[tuple[float, float, tuple]] = [(h_start, 0.0, start_state)]

        # visited[(vx,vy,vz,dir_idx,turn_count,straight_count)] = g_cost
        visited: dict[tuple, float] = {}

        # 부모 추적
        came_from: dict[tuple, tuple] = {}

        deadline = time.monotonic() + timeout_sec

        while open_heap:
            if time.monotonic() > deadline:
                return None  # timeout

            f, g, state = heapq.heappop(open_heap)
            vx, vy, vz, dir_idx, turn_count, straight_count = state

            # straight_ok: min_straight_voxels개 이상 직선 이동했는지 여부
            straight_ok = (straight_count >= min_straight_voxels)

            # 종료 조건: end_voxel과 accuracy 이내
            if self._is_near_end((vx, vy, vz), end_voxel, accuracy_voxels):
                return self._reconstruct_path(came_from, state, grid, end)

            # 이미 더 좋은 경로로 방문했으면 스킵
            state_key = (vx, vy, vz, dir_idx, min(turn_count, turn_count_limit), straight_count)
            if state_key in visited and visited[state_key] <= g:
                continue
            visited[state_key] = g

            # 이웃 확장
            for ddir in _AXIS_DIRS:
                nx, ny, nz = vx + ddir[0], vy + ddir[1], vz + ddir[2]
                next_coord = (nx, ny, nz)

                if not grid.is_in_bounds(next_coord):
                    continue
                if grid.is_blocked(next_coord):
                    continue

                new_dir_idx = _DIR_TO_IDX[ddir]
                is_turn = (dir_idx != _NO_DIR_IDX) and (dir_idx != new_dir_idx)

                # turn_count 검사
                new_turn_count = turn_count + (1 if is_turn else 0)
                if new_turn_count > turn_count_limit:
                    continue

                # min_straight 검사: 이전 꺾임 이후 min_straight 미충족 상태에서 꺾임 불허
                if is_turn and not straight_ok:
                    continue

                # straight_count 갱신
                # 꺾임: 카운터 리셋(0). 직선: 1 증가, min_straight_voxels 에서 캡
                # 캡을 두면 상태 공간 폭발 없이 "충족 여부"만 추적
                if is_turn:
                    new_straight_count = 0
                else:
                    new_straight_count = min(straight_count + 1, min_straight_voxels)

                # g-score: 이동 거리 + bending_weight × 꺾임 여부
                move_cost = vs  # 1복셀 = voxel_size mm
                bend_cost = bending_optimization_weight * vs if is_turn else 0.0
                new_g = g + move_cost + bend_cost

                next_state = (nx, ny, nz, new_dir_idx, new_turn_count, new_straight_count)
                next_state_key = (nx, ny, nz, new_dir_idx, min(new_turn_count, turn_count_limit), new_straight_count)

                if next_state_key in visited and visited[next_state_key] <= new_g:
                    continue

                h = self._heuristic((nx, ny, nz), end_voxel, vs)
                heapq.heappush(open_heap, (new_g + h, new_g, next_state))
                came_from[next_state] = state

        return None  # 경로 없음

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _heuristic(
        self,
        a: tuple[int, int, int],
        b: tuple[int, int, int],
        vs: float,
    ) -> float:
        """맨해튼 거리 × voxel_size"""
        return (abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])) * vs

    def _is_near_end(
        self,
        coord: tuple[int, int, int],
        end_voxel: tuple[int, int, int],
        accuracy_voxels: int,
    ) -> bool:
        dx = abs(coord[0] - end_voxel[0])
        dy = abs(coord[1] - end_voxel[1])
        dz = abs(coord[2] - end_voxel[2])
        return dx <= accuracy_voxels and dy <= accuracy_voxels and dz <= accuracy_voxels

    def _reconstruct_path(
        self,
        came_from: dict,
        current: tuple,
        grid: VoxelGrid,
        end_world: tuple[float, float, float],
    ) -> list[tuple[float, float, float]]:
        """역추적 → world 좌표 리스트 (시작→끝 순서)"""
        path_states: list[tuple] = []
        state = current
        while state in came_from:
            path_states.append(state)
            state = came_from[state]
        path_states.append(state)  # 시작 state
        path_states.reverse()

        world_path: list[tuple[float, float, float]] = []
        for s in path_states:
            vx, vy, vz = s[0], s[1], s[2]
            world_path.append(grid.voxel_to_world((vx, vy, vz)))

        # 종료점을 실제 end world 좌표로 교체 (snap)
        if world_path:
            world_path[-1] = end_world

        return world_path
