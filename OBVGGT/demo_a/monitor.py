"""
GPU memory and FPS monitoring utilities.
"""

import time
from dataclasses import dataclass, field

import torch


@dataclass
class FrameMetrics:
    frame_idx: int
    elapsed_sec: float
    fps: float
    peak_memory_mb: float
    current_memory_mb: float


@dataclass
class RunMetrics:
    frames: list[FrameMetrics] = field(default_factory=list)
    oom: bool = False
    oom_at_frame: int = -1
    total_elapsed_sec: float = 0.0

    @property
    def avg_fps(self) -> float:
        if not self.frames:
            return 0.0
        return len(self.frames) / sum(f.elapsed_sec for f in self.frames)

    @property
    def peak_memory_mb(self) -> float:
        if not self.frames:
            return 0.0
        return max(f.peak_memory_mb for f in self.frames)

    @property
    def memory_timeline(self) -> tuple[list[int], list[float]]:
        """Return (frame_indices, peak_memory_mb) lists for plotting."""
        xs = [f.frame_idx for f in self.frames]
        ys = [f.peak_memory_mb for f in self.frames]
        return xs, ys

    @property
    def fps_timeline(self) -> tuple[list[int], list[float]]:
        xs = [f.frame_idx for f in self.frames]
        ys = [f.fps for f in self.frames]
        return xs, ys


class GPUMonitor:
    """Context manager that tracks per-frame GPU stats."""

    def __init__(self):
        self._t0 = 0.0

    def reset(self):
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.synchronize()

    def frame_start(self):
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        self._t0 = time.perf_counter()

    def frame_end(self, frame_idx: int) -> FrameMetrics:
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        elapsed = time.perf_counter() - self._t0
        fps = 1.0 / elapsed if elapsed > 0 else 0.0

        if torch.cuda.is_available():
            peak = torch.cuda.max_memory_allocated() / 1024**2
            current = torch.cuda.memory_allocated() / 1024**2
        else:
            peak = 0.0
            current = 0.0

        return FrameMetrics(
            frame_idx=frame_idx,
            elapsed_sec=elapsed,
            fps=fps,
            peak_memory_mb=peak,
            current_memory_mb=current,
        )
