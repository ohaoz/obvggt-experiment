import numpy as np
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple

from streamvggt.utils.runtime_diagnostics import record_rope2d_call

try:
    from croco.models.curope import curope as _curope_kernels
except Exception:
    _curope_kernels = None


class PositionGetter:
    """Generates and caches 2D spatial positions for patches in a grid.

    This class efficiently manages the generation of spatial coordinates for patches
    in a 2D grid, caching results to avoid redundant computations.

    Attributes:
        position_cache: Dictionary storing precomputed position tensors for different
            grid dimensions.
    """

    def __init__(self):
        """Initializes the position generator with an empty cache."""
        self.position_cache: Dict[Tuple[int, int], torch.Tensor] = {}

    def __call__(self, batch_size: int, height: int, width: int, device: torch.device) -> torch.Tensor:
        """Generates spatial positions for a batch of patches.

        Args:
            batch_size: Number of samples in the batch.
            height: Height of the grid in patches.
            width: Width of the grid in patches.
            device: Target device for the position tensor.

        Returns:
            Tensor of shape (batch_size, height*width, 2) containing y,x coordinates
            for each position in the grid, repeated for each batch item.
        """
        if (height, width) not in self.position_cache:
            y_coords = torch.arange(height, device=device)
            x_coords = torch.arange(width, device=device)
            positions = torch.cartesian_prod(y_coords, x_coords)
            self.position_cache[height, width] = positions

        cached_positions = self.position_cache[height, width]
        return cached_positions.view(1, height * width, 2).expand(batch_size, -1, -1).clone()


class RotaryPositionEmbedding2D(nn.Module):
    """2D Rotary Position Embedding implementation.

    This module applies rotary position embeddings to input tokens based on their
    2D spatial positions. It handles the position-dependent rotation of features
    separately for vertical and horizontal dimensions.

    Args:
        frequency: Base frequency for the position embeddings. Default: 100.0
        scaling_factor: Scaling factor for frequency computation. Default: 1.0

    Attributes:
        base_frequency: Base frequency for computing position embeddings.
        scaling_factor: Factor to scale the computed frequencies.
        frequency_cache: Cache for storing precomputed frequency components.
    """

    def __init__(self, frequency: float = 100.0, scaling_factor: float = 1.0):
        """Initializes the 2D RoPE module."""
        super().__init__()
        self.base_frequency = frequency
        self.scaling_factor = scaling_factor
        self.frequency_cache: Dict[Tuple, Tuple[torch.Tensor, torch.Tensor]] = {}
        self.cuda_rope_kernel = _curope_kernels

    def _compute_frequency_components(
        self, dim: int, seq_len: int, device: torch.device, dtype: torch.dtype
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Computes frequency components for rotary embeddings.

        Args:
            dim: Feature dimension (must be even).
            seq_len: Maximum sequence length.
            device: Target device for computations.
            dtype: Data type for the computed tensors.

        Returns:
            Tuple of (cosine, sine) tensors for frequency components.
        """
        cache_key = (dim, seq_len, device, dtype)
        if cache_key not in self.frequency_cache:
            # Compute frequency bands
            exponents = torch.arange(0, dim, 2, device=device).float() / dim
            inv_freq = 1.0 / (self.base_frequency**exponents)

            # Generate position-dependent frequencies
            positions = torch.arange(seq_len, device=device, dtype=inv_freq.dtype)
            angles = torch.einsum("i,j->ij", positions, inv_freq)

            # Compute and cache frequency components
            angles = angles.to(dtype)
            angles = torch.cat((angles, angles), dim=-1)
            cos_components = angles.cos().to(dtype)
            sin_components = angles.sin().to(dtype)
            self.frequency_cache[cache_key] = (cos_components, sin_components)

        return self.frequency_cache[cache_key]

    @staticmethod
    def _rotate_features(x: torch.Tensor) -> torch.Tensor:
        """Performs feature rotation by splitting and recombining feature dimensions.

        Args:
            x: Input tensor to rotate.

        Returns:
            Rotated feature tensor.
        """
        feature_dim = x.shape[-1]
        x1, x2 = x[..., : feature_dim // 2], x[..., feature_dim // 2 :]
        return torch.cat((-x2, x1), dim=-1)

    def _apply_1d_rope(
        self, tokens: torch.Tensor, positions: torch.Tensor, cos_comp: torch.Tensor, sin_comp: torch.Tensor
    ) -> torch.Tensor:
        """Applies 1D rotary position embeddings along one dimension.

        Args:
            tokens: Input token features.
            positions: Position indices.
            cos_comp: Cosine components for rotation.
            sin_comp: Sine components for rotation.

        Returns:
            Tokens with applied rotary position embeddings.
        """
        # Embed positions with frequency components
        cos = F.embedding(positions, cos_comp)[:, None, :, :]
        sin = F.embedding(positions, sin_comp)[:, None, :, :]

        # Apply rotation
        return (tokens * cos) + (self._rotate_features(tokens) * sin)

    def forward(self, tokens: torch.Tensor, positions: torch.Tensor) -> torch.Tensor:
        """Applies 2D rotary position embeddings to input tokens.

        Args:
            tokens: Input tensor of shape (batch_size, n_heads, n_tokens, dim).
                   The feature dimension (dim) must be divisible by 4.
            positions: Position tensor of shape (batch_size, n_tokens, 2) containing
                      the y and x coordinates for each token.

        Returns:
            Tensor of same shape as input with applied 2D rotary position embeddings.

        Raises:
            AssertionError: If input dimensions are invalid or positions are malformed.
        """
        # Validate inputs
        assert tokens.size(-1) % 2 == 0, "Feature dimension must be even"
        assert positions.ndim == 3 and positions.shape[-1] == 2, "Positions must have shape (batch_size, n_tokens, 2)"

        backend_request = os.environ.get("OBVGGT_ROPE2D_BACKEND", "pytorch").strip().lower()
        if backend_request not in {"pytorch", "auto", "cuda"}:
            raise ValueError(f"Unsupported OBVGGT_ROPE2D_BACKEND={backend_request!r}")
        unsafe_curope_allowed = os.environ.get("OBVGGT_ALLOW_UNSAFE_CUROPE", "0").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        if backend_request in {"auto", "cuda"} and not unsafe_curope_allowed:
            if backend_request == "cuda":
                raise RuntimeError(
                    "cuRoPE2D is disabled for full-model inference because smoke runs hit "
                    "a process-exit invalid free. Set OBVGGT_ALLOW_UNSAFE_CUROPE=1 only for isolated microbenchmarks."
                )
            backend_request = "pytorch"

        if backend_request in {"auto", "cuda"} and self._can_use_cuda_rope(tokens, positions):
            record_rope2d_call(tokens, positions, backend="cuda_curope", module=__name__)
            return self._apply_cuda_rope(tokens, positions)
        if backend_request == "cuda":
            raise RuntimeError("OBVGGT_ROPE2D_BACKEND=cuda requested, but cuRoPE2D is unavailable or inputs are ineligible.")

        record_rope2d_call(tokens, positions, backend="pytorch_python", module=__name__)

        # Compute feature dimension for each spatial direction
        feature_dim = tokens.size(-1) // 2

        # Get frequency components
        max_position = int(positions.max()) + 1
        cos_comp, sin_comp = self._compute_frequency_components(feature_dim, max_position, tokens.device, tokens.dtype)

        # Split features for vertical and horizontal processing
        vertical_features, horizontal_features = tokens.chunk(2, dim=-1)

        # Apply RoPE separately for each dimension
        vertical_features = self._apply_1d_rope(vertical_features, positions[..., 0], cos_comp, sin_comp)
        horizontal_features = self._apply_1d_rope(horizontal_features, positions[..., 1], cos_comp, sin_comp)

        # Combine processed features
        return torch.cat((vertical_features, horizontal_features), dim=-1)

    def _can_use_cuda_rope(self, tokens: torch.Tensor, positions: torch.Tensor) -> bool:
        if self.cuda_rope_kernel is None:
            return False
        if not tokens.is_cuda or not positions.is_cuda:
            return False
        if tokens.dtype not in {torch.float16, torch.float32}:
            return False
        if tokens.ndim != 4 or positions.ndim != 3:
            return False
        if tokens.size(0) != positions.size(0) or tokens.size(2) != positions.size(1):
            return False
        if tokens.size(-1) % 4 != 0:
            return False
        return tokens.stride(-1) == 1

    def _apply_cuda_rope(self, tokens: torch.Tensor, positions: torch.Tensor) -> torch.Tensor:
        tokens_bnhd = tokens.transpose(1, 2)
        if tokens_bnhd.stride(-1) != 1 or tokens_bnhd.stride(-2) != tokens.size(-1):
            tokens_bnhd = tokens_bnhd.contiguous()
            self.cuda_rope_kernel.rope_2d(tokens_bnhd, positions.contiguous(), self.base_frequency, self.scaling_factor)
            return tokens_bnhd.transpose(1, 2).contiguous()

        self.cuda_rope_kernel.rope_2d(tokens_bnhd, positions.contiguous(), self.base_frequency, self.scaling_factor)
        return tokens
