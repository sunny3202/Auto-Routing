"""
routing_pipeline.py — RoutingPipeline 클래스

다중 배관 순차 라우팅.
완료된 경로를 즉시 장애물로 등록하여 다음 배관 충돌 방지.
SmartRoutingAI를 대체한다.
"""

import math
import time
from typing import Optional

import numpy as np

from .models import BoundingBox, RoutingEntity, RoutingOption
from .voxel_grid import VoxelGrid
from .path_finder import PathFinder


def _get_box_with_size(
    pos: tuple[float, float, float], half: float
) -> BoundingBox:
    return (
        (pos[0] - half, pos[1] - half, pos[2] - half),
        (pos[0] + half, pos[1] + half, pos[2] + half),
    )


class RoutingPipeline:
    """
    다중 배관 순차 라우팅 파이프라인.

    처리 순서:
      1. sort_pocs_fn()으로 우선순위 정렬 (XY 직선거리 짧은 순)
      2. VoxelGrid 초기화 (voxel_area_fn + restricted_area_setting_fn)
      3. entity별 start/end 오프셋 계산 → PathFinder.find_path()
      4. 성공한 경로 즉시 장애물 등록 → 다음 entity 탐색
    """

    def run(
        self,
        entities: list[RoutingEntity],
        bim_info: list[dict],
        routing_option: RoutingOption,
        progress_callback=None,
    ) -> list[RoutingEntity]:
        """
        entities: input_vaildation → preprocessing 출력 엔티티 리스트
        bim_info: BIM JSON의 obstacles 리스트
        routing_option: RoutingOption 인스턴스 (콜백 포함)
        progress_callback: (float 0~100) → None, 진행률 전달용

        반환: path가 채워진 entities (실패 entity는 path = [])
        """
        if not entities:
            return entities

        opt = routing_option

        # 1. 정렬
        if opt.sort_pocs_fn is not None:
            entities = opt.sort_pocs_fn(entities)

        # 2. 장애물 목록 준비
        obstacles: list[BoundingBox] = self._build_obstacles(bim_info, opt)

        # 3. VoxelGrid 초기화
        voxel_size = opt.voxel_size  # 300mm 고정
        area = self._get_voxel_area(entities, obstacles, opt)
        grid = VoxelGrid(area, voxel_size)

        # 장애물 마킹
        for box in obstacles:
            grid.mark_obstacle(box)

        finder = PathFinder()
        total = len(entities)

        # 4. 순차 라우팅
        for idx, entity in enumerate(entities):
            if progress_callback:
                progress_callback(idx / total * 100)

            # start/end 오프셋 계산
            start_world = self._get_start(entity, opt)
            end_world = self._get_end(entity, opt)

            # 탐색
            path = finder.find_path(
                start=start_world,
                end=end_world,
                grid=grid,
                turn_count_limit=opt.turn_count_limit,
                min_straight_distance=opt.min_straight_distance,
                bending_optimization_weight=opt.bending_optimization_weight,
                accuracy=opt.accuracy,
                timeout_sec=30.0,
            )

            if path is not None and len(path) >= 2:
                entity["path"] = path
                # 완료 경로를 즉시 장애물로 등록
                self._mark_path_as_obstacle(grid, path, entity)
            else:
                entity["path"] = []

        if progress_callback:
            progress_callback(100.0)

        return entities

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _build_obstacles(
        self, bim_info: list[dict], opt: RoutingOption
    ) -> list[BoundingBox]:
        """bim_info obstacles → BoundingBox 리스트"""
        obstacles: list[BoundingBox] = []

        def _parse_coord(s: str) -> tuple[float, float, float]:
            # "X:-1000, Y:-2000, Z:777" 형식 파싱
            parts = [p.strip() for p in s.split(",")]
            vals = {}
            for p in parts:
                k, v = p.split(":")
                vals[k.strip()] = float(v.strip())
            return (vals["X"], vals["Y"], vals["Z"])

        for obs in bim_info:
            try:
                mn = _parse_coord(obs["min"])
                mx = _parse_coord(obs["max"])
                obstacles.append((mn, mx))
            except Exception:
                # bounding_box 튜플 형식이면 그대로 사용
                try:
                    bb = obs.get("bounding_box") or obs
                    if isinstance(bb, (list, tuple)) and len(bb) == 2:
                        obstacles.append((tuple(bb[0]), tuple(bb[1])))
                except Exception:
                    pass

        # restricted_area_setting_fn 필터 적용
        if opt.restricted_area_setting_fn is not None:
            bim_typed = bim_info  # RuleSet이 BIMInfo 타입으로 넘김
            try:
                obstacles = opt.restricted_area_setting_fn(bim_typed, [])
            except Exception:
                pass

        return obstacles

    def _get_voxel_area(
        self,
        entities: list[RoutingEntity],
        obstacles: list[BoundingBox],
        opt: RoutingOption,
    ) -> BoundingBox:
        """voxel_area_fn 호출 또는 entities 기반 자동 계산"""
        if opt.voxel_area_fn is not None:
            try:
                return opt.voxel_area_fn(entities, obstacles)
            except Exception:
                pass

        # 자동: 모든 start/end + 5000mm 패딩
        if not entities:
            return ((0, 0, 0), (1000, 1000, 1000))

        xs, ys, zs = [], [], []
        for e in entities:
            for pt in [e["start"], e["end"]]:
                xs.append(pt[0]); ys.append(pt[1]); zs.append(pt[2])

        PAD = 5000
        return (
            (min(xs) - PAD, min(ys) - PAD, min(zs) - PAD),
            (max(xs) + PAD, max(ys) + PAD, max(zs) + PAD),
        )

    def _get_start(
        self, entity: RoutingEntity, opt: RoutingOption
    ) -> tuple[float, float, float]:
        if opt.processing_entity_start_fn is not None:
            try:
                return opt.processing_entity_start_fn(entity, opt)
            except Exception:
                pass
        return entity["start"]

    def _get_end(
        self, entity: RoutingEntity, opt: RoutingOption
    ) -> tuple[float, float, float]:
        if opt.processing_entity_end_fn is not None:
            try:
                return opt.processing_entity_end_fn(entity, opt)
            except Exception:
                pass
        return entity["end"]

    def _mark_path_as_obstacle(
        self, grid: VoxelGrid, path: list[tuple], entity: RoutingEntity
    ) -> None:
        """완료 경로 복셀을 장애물로 마킹 (diameter + spacing 기반 반경)"""
        diameter = entity.get("diameter", 0) or 0
        spacing = entity.get("spacing", 0) or 0
        half = (diameter / 2 + spacing)

        for pt in path:
            box = _get_box_with_size(pt, half)
            grid.mark_obstacle(box)
