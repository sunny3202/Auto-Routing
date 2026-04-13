"""
voxel_grid.py — VoxelGrid 클래스

numpy 3D boolean array 기반 복셀 공간.
장애물 마킹, 충돌 검사, 좌표 변환을 담당.
"""

import numpy as np
from .models import BoundingBox


class VoxelGrid:
    """
    3D 복셀 격자. 모든 좌표는 mm 단위.

    world 좌표 → voxel 인덱스: floor((pos - origin) / voxel_size)
    voxel 인덱스 → world 좌표 (복셀 중심): origin + idx * voxel_size + voxel_size/2
    """

    def __init__(self, area: BoundingBox, voxel_size: float):
        self.voxel_size = voxel_size
        self.origin = np.array(area[0], dtype=float)

        # 격자 크기 계산 (최소 1)
        span = np.array(area[1], dtype=float) - self.origin
        self.shape = tuple(
            max(1, int(np.ceil(span[i] / voxel_size))) for i in range(3)
        )  # (nx, ny, nz)

        # False = 통과 가능, True = 장애물
        self._grid: np.ndarray = np.zeros(self.shape, dtype=bool)

    # ------------------------------------------------------------------
    # 좌표 변환
    # ------------------------------------------------------------------

    def world_to_voxel(self, pos: tuple) -> tuple[int, int, int]:
        """world 좌표(mm) → 복셀 인덱스 (클램프 포함)"""
        idx = (np.array(pos, dtype=float) - self.origin) / self.voxel_size
        ix = int(np.clip(int(idx[0]), 0, self.shape[0] - 1))
        iy = int(np.clip(int(idx[1]), 0, self.shape[1] - 1))
        iz = int(np.clip(int(idx[2]), 0, self.shape[2] - 1))
        return (ix, iy, iz)

    def voxel_to_world(self, coord: tuple[int, int, int]) -> tuple[float, float, float]:
        """복셀 인덱스 → world 좌표(mm, 복셀 중심)"""
        center = self.origin + np.array(coord, dtype=float) * self.voxel_size + self.voxel_size / 2
        return (float(center[0]), float(center[1]), float(center[2]))

    # ------------------------------------------------------------------
    # 장애물 마킹
    # ------------------------------------------------------------------

    def mark_obstacle(self, box: BoundingBox) -> None:
        """BoundingBox(mm)에 해당하는 복셀을 장애물로 마킹"""
        mn = np.array(box[0], dtype=float)
        mx = np.array(box[1], dtype=float)

        ix_min = max(0, int(np.floor((mn[0] - self.origin[0]) / self.voxel_size)))
        iy_min = max(0, int(np.floor((mn[1] - self.origin[1]) / self.voxel_size)))
        iz_min = max(0, int(np.floor((mn[2] - self.origin[2]) / self.voxel_size)))
        ix_max = min(self.shape[0] - 1, int(np.floor((mx[0] - self.origin[0]) / self.voxel_size)))
        iy_max = min(self.shape[1] - 1, int(np.floor((mx[1] - self.origin[1]) / self.voxel_size)))
        iz_max = min(self.shape[2] - 1, int(np.floor((mx[2] - self.origin[2]) / self.voxel_size)))

        if ix_min > ix_max or iy_min > iy_max or iz_min > iz_max:
            return

        self._grid[ix_min:ix_max+1, iy_min:iy_max+1, iz_min:iz_max+1] = True

    def mark_obstacle_sphere(
        self, center: tuple, radius: float
    ) -> None:
        """완료 경로 점 주변을 구형으로 마킹 (배관 직경 기반)"""
        cx, cy, cz = center
        r = radius
        box: BoundingBox = (
            (cx - r, cy - r, cz - r),
            (cx + r, cy + r, cz + r),
        )
        self.mark_obstacle(box)

    def is_blocked(self, voxel_coord: tuple[int, int, int]) -> bool:
        """복셀이 장애물인지 확인"""
        ix, iy, iz = voxel_coord
        if ix < 0 or iy < 0 or iz < 0:
            return True
        if ix >= self.shape[0] or iy >= self.shape[1] or iz >= self.shape[2]:
            return True
        return bool(self._grid[ix, iy, iz])

    # ------------------------------------------------------------------
    # 유틸리티
    # ------------------------------------------------------------------

    def is_in_bounds(self, coord: tuple[int, int, int]) -> bool:
        ix, iy, iz = coord
        return (
            0 <= ix < self.shape[0]
            and 0 <= iy < self.shape[1]
            and 0 <= iz < self.shape[2]
        )

    def count_obstacles(self) -> int:
        return int(np.sum(self._grid))

    def total_voxels(self) -> int:
        return self._grid.size
