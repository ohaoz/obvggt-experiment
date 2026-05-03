import torch
import torch.nn as nn
from huggingface_hub import PyTorchModelHubMixin  # used for model hub

from streamvggt.models.aggregator import Aggregator
from streamvggt.utils.obcache_kv import StreamOBCacheLayerState
from streamvggt.heads.camera_head import CameraHead
from streamvggt.heads.dpt_head import DPTHead
from streamvggt.heads.track_head import TrackHead
from streamvggt.utils.phase_profile import phase_profile_end, phase_profile_start
from streamvggt.utils.runtime_diagnostics import snapshot_runtime_diagnostics
from transformers.file_utils import ModelOutput
from typing import Optional, Tuple, List, Any, Dict
from dataclasses import dataclass

@dataclass
class StreamVGGTOutput(ModelOutput):
    ress: Optional[List[dict]] = None
    views: Optional[torch.Tensor] = None
    kv_cache_stats: Optional[Dict[str, float]] = None
    runtime_diagnostics: Optional[Dict[str, Any]] = None

class StreamVGGT(nn.Module, PyTorchModelHubMixin):
    def __init__(self, img_size=518, patch_size=14, embed_dim=1024):
        super().__init__()

        self.aggregator = Aggregator(img_size=img_size, patch_size=patch_size, embed_dim=embed_dim)
        self.camera_head = CameraHead(dim_in=2 * embed_dim)
        self.point_head = DPTHead(dim_in=2 * embed_dim, output_dim=4, activation="inv_log", conf_activation="expp1")
        self.depth_head = DPTHead(dim_in=2 * embed_dim, output_dim=2, activation="exp", conf_activation="expp1")
        self.track_head = TrackHead(dim_in=2 * embed_dim, patch_size=patch_size)
    


    def _collect_kv_cache_stats(self, past_key_values) -> Dict[str, float]:
        if past_key_values is None:
            return {}

        total_layers = int(len(past_key_values))
        obcache_layers = 0
        layer_lengths = []
        total_evict_calls = 0
        total_evicted_tokens = 0
        total_appended_tokens = 0
        total_reused_tokens = 0
        max_seq_len_seen = 0
        profile_totals: Dict[str, float] = {}

        for layer_cache in past_key_values:
            if layer_cache is None:
                continue

            if isinstance(layer_cache, StreamOBCacheLayerState):
                obcache_layers += 1
                layer_lengths.append(int(layer_cache.k.size(-2)))
                snap = layer_cache.snapshot()
                total_evict_calls += int(snap.get("evict_calls", 0))
                total_evicted_tokens += int(snap.get("evicted_tokens_total", 0))
                total_appended_tokens += int(snap.get("appended_tokens_total", 0))
                total_reused_tokens += int(snap.get("reused_tokens_total", 0))
                max_seq_len_seen = max(max_seq_len_seen, int(snap.get("max_seq_len_seen", 0)))
                for key, value in snap.items():
                    if key.startswith("profile_"):
                        profile_totals[key] = profile_totals.get(key, 0.0) + float(value)
            elif isinstance(layer_cache, (tuple, list)) and len(layer_cache) >= 1 and torch.is_tensor(layer_cache[0]):
                layer_lengths.append(int(layer_cache[0].size(-2)))

        stats = {
            "total_layers": float(total_layers),
            "obcache_layers": float(obcache_layers),
            "has_obcache_stats": float(1 if obcache_layers > 0 else 0),
            "cache_tokens_mean": float(sum(layer_lengths) / len(layer_lengths)) if layer_lengths else 0.0,
            "cache_tokens_min": float(min(layer_lengths)) if layer_lengths else 0.0,
            "cache_tokens_max": float(max(layer_lengths)) if layer_lengths else 0.0,
            "max_seq_len_seen": float(max_seq_len_seen),
            "evict_calls": float(total_evict_calls),
            "evicted_tokens_total": float(total_evicted_tokens),
            "appended_tokens_total": float(total_appended_tokens),
            "reused_tokens_total": float(total_reused_tokens),
        }
        denom = total_appended_tokens + total_reused_tokens
        stats["cache_hit_rate"] = float(total_reused_tokens / denom) if denom > 0 else 0.0
        stats.update(profile_totals)
        return stats

    def forward(
        self,
        views,
        query_points: torch.Tensor = None,
        history_info: Optional[dict] = None,
    ):
        images = torch.stack(
            [view["img"] for view in views], dim=0
        ).permute(1, 0, 2, 3, 4)    # B S C H W

        # If without batch dimension, add it
        if len(images.shape) == 4:
            images = images.unsqueeze(0)
        if query_points is not None and len(query_points.shape) == 2:
            query_points = query_points.unsqueeze(0)

        if history_info is None:
            history_info = {"token": None}

        aggregated_tokens_list, patch_start_idx = self.aggregator(images)
        predictions = {}

        with torch.cuda.amp.autocast(enabled=False):
            if self.camera_head is not None:
                pose_enc_list = self.camera_head(aggregated_tokens_list)
                predictions["pose_enc"] = pose_enc_list[-1]  # pose encoding of the last iteration

            if self.depth_head is not None:
                depth, depth_conf = self.depth_head(
                    aggregated_tokens_list, images=images, patch_start_idx=patch_start_idx
                )
                predictions["depth"] = depth
                predictions["depth_conf"] = depth_conf

            if self.point_head is not None:
                pts3d, pts3d_conf = self.point_head(
                    aggregated_tokens_list, images=images, patch_start_idx=patch_start_idx
                )
                predictions["world_points"] = pts3d
                predictions["world_points_conf"] = pts3d_conf

            if self.track_head is not None and query_points is not None:
                track_list, vis, conf = self.track_head(
                    aggregated_tokens_list, images=images, patch_start_idx=patch_start_idx, query_points=query_points
                )
                predictions["track"] = track_list[-1]  # track of the last iteration
                predictions["vis"] = vis
                predictions["conf"] = conf
            predictions["images"] = images

            B, S = images.shape[:2]
            ress = []
            for s in range(S):
                res = {
                    'pts3d_in_other_view': predictions['world_points'][:, s],  # [B, H, W, 3]
                    'conf': predictions['world_points_conf'][:, s],  # [B, H, W]

                    'depth': predictions['depth'][:, s],  # [B, H, W, 1]
                    'depth_conf': predictions['depth_conf'][:, s],  # [B, H, W]
                    'camera_pose': predictions['pose_enc'][:, s, :],  # [B, 9]

                    **({'valid_mask': views[s]["valid_mask"]}
                    if 'valid_mask' in views[s] else {}),  # [B, H, W]

                    **({'track': predictions['track'][:, s],  # [B, N, 2]
                        'vis': predictions['vis'][:, s],  # [B, N]
                        'track_conf': predictions['conf'][:, s]}
                    if 'track' in predictions else {})
                }
                ress.append(res)
            return StreamVGGTOutput(ress=ress, views=views)  # [S] [B, C, H, W]
        
    def inference(
        self,
        frames,
        query_points: torch.Tensor = None,
        past_key_values=None,
        kv_cache_cfg: Optional[dict] = None,
        output_keys: Optional[List[str]] = None,
    ):
        requested_outputs = self._normalize_inference_output_keys(output_keys)
        run_depth = "depth" in requested_outputs
        run_camera = "camera" in requested_outputs
        run_points = "points" in requested_outputs
        run_track = "track" in requested_outputs

        if past_key_values is None:
            past_key_values = [None] * self.aggregator.depth
        past_key_values_camera = (
            [None] * self.camera_head.trunk_depth
            if run_camera and self.camera_head is not None
            else None
        )
        
        all_ress = []
        processed_frames = []

        for i, frame in enumerate(frames):
            images = frame["img"].unsqueeze(0) 
            aggregator_output = self.aggregator(
                images, 
                past_key_values=past_key_values,
                use_cache=True, 
                past_frame_idx=i,
                obcache_cfg=kv_cache_cfg,
            )
            
            if isinstance(aggregator_output, tuple) and len(aggregator_output) == 3:
                aggregated_tokens, patch_start_idx, past_key_values = aggregator_output
            else:
                aggregated_tokens, patch_start_idx = aggregator_output
            
            with torch.cuda.amp.autocast(enabled=False):
                frame_outputs = {}
                heads_total_phase = phase_profile_start("heads_total", aggregated_tokens)

                if run_camera and self.camera_head is not None:
                    camera_phase = phase_profile_start("head_camera", aggregated_tokens)
                    pose_enc, past_key_values_camera = self.camera_head(aggregated_tokens, past_key_values_camera=past_key_values_camera, use_cache=True)
                    pose_enc = pose_enc[-1]
                    frame_outputs['camera_pose'] = pose_enc[:, 0, :]
                    phase_profile_end(camera_phase, aggregated_tokens)

                if run_depth and self.depth_head is not None:
                    depth_phase = phase_profile_start("head_depth", aggregated_tokens)
                    depth, depth_conf = self.depth_head(
                        aggregated_tokens, images=images, patch_start_idx=patch_start_idx
                    )
                    frame_outputs['depth'] = depth[:, 0]
                    frame_outputs['depth_conf'] = depth_conf[:, 0]
                    phase_profile_end(depth_phase, aggregated_tokens)
                
                if run_points and self.point_head is not None:
                    points_phase = phase_profile_start("head_points", aggregated_tokens)
                    pts3d, pts3d_conf = self.point_head(
                        aggregated_tokens, images=images, patch_start_idx=patch_start_idx
                    )
                    frame_outputs['pts3d_in_other_view'] = pts3d[:, 0]
                    frame_outputs['conf'] = pts3d_conf[:, 0]
                    phase_profile_end(points_phase, aggregated_tokens)

                if run_track and self.track_head is not None and query_points is not None:
                    track_phase = phase_profile_start("head_track", aggregated_tokens)
                    track_list, vis, conf = self.track_head(
                        aggregated_tokens, images=images, patch_start_idx=patch_start_idx, query_points=query_points
                )
                    track = track_list[-1][:, 0]  
                    query_points = track
                    frame_outputs['track'] = track
                    frame_outputs['vis'] = vis[:, 0]
                    frame_outputs['track_conf'] = conf[:, 0]
                    phase_profile_end(track_phase, aggregated_tokens)
                phase_profile_end(heads_total_phase, aggregated_tokens)

            res = dict(frame_outputs)
            if 'valid_mask' in frame:
                res['valid_mask'] = frame["valid_mask"]
            all_ress.append(res)
            processed_frames.append(frame)
        
        kv_cache_stats = self._collect_kv_cache_stats(past_key_values)
        output = StreamVGGTOutput(
            ress=all_ress,
            views=processed_frames,
            kv_cache_stats=kv_cache_stats,
            runtime_diagnostics=snapshot_runtime_diagnostics(),
        )
        return output

    @staticmethod
    def _normalize_inference_output_keys(output_keys: Optional[List[str]]) -> set:
        if output_keys is None:
            return {"camera", "depth", "points", "track"}
        normalized = set()
        for key in output_keys:
            value = str(key).strip().lower()
            if value in {"all", "full"}:
                return {"camera", "depth", "points", "track"}
            if value in {"camera", "camera_pose", "pose", "pose_enc"}:
                normalized.add("camera")
            elif value in {"depth", "depth_conf"}:
                normalized.add("depth")
            elif value in {"points", "point", "pts3d", "world_points", "pts3d_in_other_view", "conf"}:
                normalized.add("points")
            elif value in {"track", "tracks", "vis", "track_conf"}:
                normalized.add("track")
            else:
                raise ValueError(f"Unsupported inference output key: {key}")
        return normalized
