#!/usr/bin/env python3
"""Measure every native decoded RGB frame without resampling its timeline.

This is evidence collection, not semantic animation recognition or a claim of
pixel-identical reconstruction. Source videos and full-resolution evidence stay
in the user's project. Requires PyAV, NumPy, Pillow and a local C compiler.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import ctypes
from datetime import datetime, timezone
import gzip
import hashlib
import heapq
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

VERSION = "1.0.1"
# One native-resolution pixel traversal. RGB sums and counts are exact integers;
# only their serialized means are rounded. Histograms deliberately have 8 bins
# per RGB channel (32-code-value ranges), not imaginary exact palette colors.
C_KERNEL = r"""

#include <stdint.h>
#include <stddef.h>
#ifdef __aarch64__
#include <arm_neon.h>
#endif
void measure(const uint8_t *rgb, const uint8_t *previous, int w, int h,
             int grid, uint64_t *sums, uint64_t *diffs, uint64_t *hist) {
    for (int gy=0; gy<grid; ++gy) {
        int y0=gy*h/grid, y1=(gy+1)*h/grid;
        for (int gx=0; gx<grid; ++gx) {
            int x0=gx*w/grid, x1=(gx+1)*w/grid;
            int cell=gy*grid+gx;
            uint64_t rsum=0,gsum=0,bsum=0,drsum=0,dgsum=0,dbsum=0;
            #ifdef __aarch64__
            uint32x4_t ar=vdupq_n_u32(0),ag=ar,ab=ar,adr=ar,adg=ar,adb=ar;
#endif
            for (int y=y0; y<y1; ++y) {
                size_t i=((size_t)y*w+x0)*3;
                int x=x0;
#ifdef __aarch64__
                for (; x+16<=x1; x+=16,i+=48) {
                    uint8x16x3_t a=vld3q_u8(rgb+i);
                    ar=vaddq_u32(ar,vpaddlq_u16(vpaddlq_u8(a.val[0])));
                    ag=vaddq_u32(ag,vpaddlq_u16(vpaddlq_u8(a.val[1])));
                    ab=vaddq_u32(ab,vpaddlq_u16(vpaddlq_u8(a.val[2])));
                    if(previous) {
                        uint8x16x3_t b=vld3q_u8(previous+i);
                        adr=vaddq_u32(adr,vpaddlq_u16(vpaddlq_u8(vabdq_u8(a.val[0],b.val[0]))));
                        adg=vaddq_u32(adg,vpaddlq_u16(vpaddlq_u8(vabdq_u8(a.val[1],b.val[1]))));
                        adb=vaddq_u32(adb,vpaddlq_u16(vpaddlq_u8(vabdq_u8(a.val[2],b.val[2]))));
                    }
                    for(int k=0;k<16;k++) {
                        int j=i+k*3;
                        hist[((rgb[j]>>5)<<6)|((rgb[j+1]>>5)<<3)|(rgb[j+2]>>5)]++;
                    }
                }
#endif
                for (; x<x1; ++x,i+=3) {
                    int r=rgb[i],g=rgb[i+1],b=rgb[i+2];
                    rsum+=r; gsum+=g; bsum+=b;
                    hist[((r>>5)<<6)|((g>>5)<<3)|(b>>5)]++;
                    if (previous) {
                        int dr=r-previous[i],dg=g-previous[i+1],db=b-previous[i+2];
                        drsum+=dr<0?-dr:dr;
                        dgsum+=dg<0?-dg:dg;
                        dbsum+=db<0?-db:db;
                    }
                }
            }
            #ifdef __aarch64__
            rsum+=vaddvq_u32(ar);gsum+=vaddvq_u32(ag);bsum+=vaddvq_u32(ab);
            drsum+=vaddvq_u32(adr);dgsum+=vaddvq_u32(adg);dbsum+=vaddvq_u32(adb);
#endif
            sums[cell*3]=rsum; sums[cell*3+1]=gsum; sums[cell*3+2]=bsum;
            diffs[cell*3]=drsum; diffs[cell*3+1]=dgsum; diffs[cell*3+2]=dbsum;
        }
    }
}
"""


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def build_kernel(cache_dir):
    compiler = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    if not compiler:
        raise RuntimeError("A local C compiler is required; no downsampled fallback is used")
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(C_KERNEL.encode()).hexdigest()
    suffix = ".dylib" if os.uname().sysname == "Darwin" else ".so"
    library = cache_dir / ("frame-stats-" + digest[:16] + suffix)
    if not library.exists():
        with tempfile.TemporaryDirectory(dir=cache_dir) as temporary:
            temporary = Path(temporary)
            source = temporary / "stats.c"
            compiled = temporary / ("stats" + suffix)
            source.write_text(C_KERNEL)
            subprocess.run([compiler, "-O3", "-shared", "-fPIC", str(source),
                            "-o", str(compiled)], check=True, capture_output=True)
            compiled.replace(library)
    return str(library.resolve()), digest


def probe(path):
    return json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_streams",
         "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, check=True).stdout)


def read_transcript(source):
    path = Path(source).parent / "transcript.srt"
    if not path.is_file():
        return [], None
    cue_pattern = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
        r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*\n(.*?)(?=\n\s*\n|\Z)", re.S)
    cues = []
    for match in cue_pattern.finditer(path.read_text(errors="replace")):
        numbers = [int(n) for n in match.groups()[:8]]
        start = numbers[0]*3600+numbers[1]*60+numbers[2]+numbers[3]/1000
        end = numbers[4]*3600+numbers[5]*60+numbers[6]+numbers[7]/1000
        text = re.sub(r"\s+", " ", match.group(9)).strip()
        cues.append({"start": start, "end": end, "text": text})
    return cues, {"path": str(path), "sha256": sha256(path),
                  "basis": "existing machine ASR; not human-approved transcription"}


def process_source(job):
    import av
    import numpy as np
    from PIL import Image

    started = time.monotonic()
    source = Path(job["source"]).resolve()
    output = Path(job["output"]).resolve()
    if output == source or source in output.parents:
        raise ValueError("Output must not overwrite or be inside the source video")
    output.mkdir(parents=True, exist_ok=True)
    source_hash = sha256(source)
    if job.get("expected_sha256") and source_hash != job["expected_sha256"]:
        raise ValueError(f"Source hash changed for rank {job['rank']}")
    identity = {"version": VERSION, "script_sha256": sha256(__file__),
                "kernel_sha256": job["kernel_sha256"], "source_sha256": source_hash,
                "grid": job["grid"], "evidence_frames": job["evidence_frames"],
                "histogram_bins_per_rgb_channel": 8}
    summary_path = output / "inventory.json"
    if summary_path.exists() and not job["overwrite"]:
        cached = json.loads(summary_path.read_text())
        ledger = output / "frames.jsonl.gz"
        if (cached.get("identity") == identity and cached.get("status") == "complete"
                and ledger.is_file() and sha256(ledger) == cached.get("ledger_sha256")
                and all((output / frame["path"]).is_file()
                        and sha256(output / frame["path"]) == frame["sha256"]
                        for frame in cached.get("evidence", []))):
            return cached | {"cache_reused": True}
        raise ValueError(f"Inventory at {output} changed; use --overwrite to regenerate")
    native_probe = probe(source)
    atomic_json(output / "source-metadata.json", native_probe)
    library = ctypes.CDLL(job["kernel_library"])
    u8pointer = ctypes.POINTER(ctypes.c_uint8)
    u64pointer = ctypes.POINTER(ctypes.c_uint64)
    measure = library.measure
    measure.argtypes = [u8pointer, u8pointer, ctypes.c_int, ctypes.c_int,
                        ctypes.c_int, u64pointer, u64pointer, u64pointer]
    measure.restype = None
    grid = job["grid"]
    hist_total = np.zeros(512, dtype=np.uint64)
    sums_total = np.zeros(3, dtype=np.uint64)
    pixel_total = 0
    previous = None
    previous_hist = None
    previous_time = None
    first_time = None
    last_time = None
    frame_intervals = []
    dimensions = set()
    cut_candidates = []
    motion_peaks = []
    evidence = []
    evidence_dir = output / "native-frames"
    evidence_dir.mkdir(exist_ok=True)
    ledger = output / "frames.jsonl.gz"
    temporary_ledger = output / "frames.jsonl.gz.part"
    frame_count = 0
    pts_missing = 0
    pts_non_increasing = 0
    maximum_frame_rgb_mad = 0.0
    av.logging.set_level(av.logging.WARNING)
    with av.open(str(source)) as container:
        stream = container.streams.video[0]
        stream.thread_type = "AUTO"
        stream.codec_context.thread_count = 1
        declared_frames = stream.frames
        declared_duration = (float(stream.duration * stream.time_base)
                             if stream.duration is not None else float(container.duration or 0)/1e6)
        anchor_count = job["evidence_frames"]
        anchors = np.linspace(0, max(0, declared_duration - 1/30), anchor_count).tolist()
        next_anchor = 0
        with av.logging.Capture(local=True) as decode_logs, gzip.open(
                temporary_ledger, "wt", encoding="utf-8", compresslevel=1) as writer:
            for frame in container.decode(stream):
                # No seek, fps filter, resize, interpolation or skipped frame.
                rgb = frame.to_ndarray(format="rgb24")
                if not rgb.flags.c_contiguous:
                    rgb = np.ascontiguousarray(rgb)
                height, width = rgb.shape[:2]
                if previous is not None and previous.shape != rgb.shape:
                    previous = None
                dimensions.add((width, height))
                cells = grid * grid
                sums = np.zeros((cells, 3), dtype=np.uint64)
                diffs = np.zeros((cells, 3), dtype=np.uint64)
                histogram = np.zeros(512, dtype=np.uint64)
                measure(rgb.ctypes.data_as(u8pointer),
                        previous.ctypes.data_as(u8pointer) if previous is not None else None,
                        width, height, grid, sums.ctypes.data_as(u64pointer),
                        diffs.ctypes.data_as(u64pointer), histogram.ctypes.data_as(u64pointer))
                weights = np.array([((gy+1)*height//grid - gy*height//grid)
                                    *((gx+1)*width//grid - gx*width//grid)
                                    for gy in range(grid) for gx in range(grid)], dtype=np.uint64)
                mean_rgb = sums.sum(axis=0, dtype=np.uint64).astype(float)/(width*height)
                grid_mean = sums.astype(float)/weights[:, None]
                diff_rgb = (diffs.sum(axis=0, dtype=np.uint64).astype(float)/(width*height)
                            if previous is not None else None)
                mad = float(diff_rgb.mean()) if diff_rgb is not None else 0.0
                grid_mad = (diffs.sum(axis=1, dtype=np.uint64).astype(float)/(weights*3)
                            if previous is not None else None)
                hist_l1 = (float(np.abs(histogram.astype(float)/(width*height)
                                         - previous_hist).sum())
                           if previous_hist is not None else 0.0)
                pts = frame.pts
                frame_time = float(pts * frame.time_base) if pts is not None else None
                if frame_time is None:
                    pts_missing += 1
                else:
                    if first_time is None:
                        first_time = frame_time
                    if previous_time is not None:
                        difference = frame_time - previous_time
                        if difference <= 0:
                            pts_non_increasing += 1
                        frame_intervals.append(difference)
                    previous_time = frame_time
                    last_time = frame_time
                record = {
                    "frame_no": frame_count, "pts": pts,
                    "time_base": [frame.time_base.numerator, frame.time_base.denominator],
                    "pts_seconds": frame_time, "width": width, "height": height,
                    "key_frame": bool(frame.key_frame),
                    "rgb_mean": np.round(mean_rgb, 6).tolist(),
                    "grid_rgb_mean_row_major": np.round(grid_mean, 6).tolist(),
                    "rgb_histogram_8x8x8_counts": histogram.tolist(),
                    "rgb_mad_from_previous": round(mad, 6) if previous is not None else None,
                    "grid_rgb_mad_from_previous": (np.round(grid_mad, 6).tolist()
                                                    if grid_mad is not None else None),
                    "histogram_l1_from_previous": round(hist_l1, 6) if previous_hist is not None else None,
                }
                writer.write(json.dumps(record, separators=(",", ":")) + "\n")
                if mad >= 18 and hist_l1 >= .18:
                    cut_candidates.append({"frame_no": frame_count, "pts_seconds": frame_time,
                                           "rgb_mad": round(mad, 6), "histogram_l1": round(hist_l1, 6),
                                           "status": "machine candidate; semantic review pending"})
                peak = (mad, frame_count, frame_time)
                if len(motion_peaks) < 20:
                    heapq.heappush(motion_peaks, peak)
                elif mad > motion_peaks[0][0]:
                    heapq.heapreplace(motion_peaks, peak)
                if (frame_time is not None and next_anchor < len(anchors)
                        and frame_time >= anchors[next_anchor]):
                    name = f"native-frames/frame-{frame_count:07d}.png"
                    Image.fromarray(rgb).save(output / name, compress_level=1)
                    evidence.append({"frame_no": frame_count, "pts": pts,
                                     "pts_seconds": frame_time, "path": name,
                                     "width": width, "height": height,
                                     "sha256": sha256(output / name),
                                     "purpose": "full-span native RGB evidence; not an exact palette inference"})
                    while next_anchor < len(anchors) and frame_time >= anchors[next_anchor]:
                        next_anchor += 1
                hist_total += histogram
                sums_total += sums.sum(axis=0, dtype=np.uint64)
                pixel_total += width*height
                maximum_frame_rgb_mad = max(maximum_frame_rgb_mad, mad)
                previous = rgb
                previous_hist = histogram.astype(float)/(width*height)
                frame_count += 1
                if frame_count % 900 == 0:
                    print(json.dumps({"rank": job["rank"], "processed_frames": frame_count,
                                      "pts_seconds": frame_time,
                                      "elapsed_seconds": round(time.monotonic()-started, 1)}), flush=True)
        logs = [{"level": int(level), "component": name, "message": message.strip()}
                for level, name, message in decode_logs]
    if not frame_count:
        raise ValueError("Source decoded no video frames")
    if pts_missing or pts_non_increasing:
        raise ValueError("Native PTS missing or non-increasing; timeline must be reviewed")
    if any(log["level"] <= av.logging.ERROR for log in logs):
        atomic_json(output / "decode-errors.json", logs)
        raise ValueError("Decoder reported errors; full source decode is not accepted")
    if declared_frames and frame_count != declared_frames:
        raise ValueError(f"Decoded frame count {frame_count} differs from container {declared_frames}")
    # The encoded stream end need not coincide with an evenly spaced anchor.
    # Always retain the final decoded native frame as exact full-span evidence.
    if not evidence or evidence[-1]["frame_no"] != frame_count - 1:
        name = f"native-frames/frame-{frame_count-1:07d}.png"
        Image.fromarray(previous).save(output / name, compress_level=1)
        evidence.append({"frame_no": frame_count-1, "pts": frame.pts,
                         "pts_seconds": last_time, "path": name,
                         "width": previous.shape[1], "height": previous.shape[0],
                         "sha256": sha256(output / name),
                         "purpose": "final decoded native RGB frame"})
    temporary_ledger.replace(ledger)
    intervals = np.asarray(frame_intervals)
    mode_dt = float(np.median(intervals)) if len(intervals) else None
    source_end = last_time + mode_dt if mode_dt is not None else last_time
    cues, transcript_basis = read_transcript(source)
    # Full source coverage in bounded intervals; each remains semantically unreviewed.
    clusters = []
    for candidate in cut_candidates:
        if clusters and candidate["pts_seconds"] - clusters[-1]["end"] <= .35:
            clusters[-1]["end"] = candidate["pts_seconds"]
            clusters[-1]["frame_count"] += 1
            if candidate["rgb_mad"] > clusters[-1]["peak"]["rgb_mad"]:
                clusters[-1]["peak"] = candidate
        else:
            clusters.append({"start": candidate["pts_seconds"],
                             "end": candidate["pts_seconds"], "frame_count": 1,
                             "peak": candidate,
                             "status": "machine transition/cut candidate; semantic audit pending"})
    atomic_json(output / "transition-clusters.json", clusters)
    boundaries = {float(first_time), float(source_end)}
    boundaries.update(float(first_time) + i*10 for i in range(1, int((source_end-first_time)//10)+1))
    boundaries.update(float(cluster["start"]) for cluster in clusters)
    boundaries.update(min(source_end, float(cluster["end"])+(mode_dt or 0)) for cluster in clusters)
    boundaries = sorted(t for t in boundaries if first_time <= t <= source_end)
    semantic_segments = []
    for index, (start, end) in enumerate(zip(boundaries, boundaries[1:])):
        if end-start < .001:
            continue
        cue_text = " ".join(cue["text"] for cue in cues if cue["end"] > start and cue["start"] < end)
        semantic_segments.append({
            "segment_no": index, "start": round(start, 6), "end": round(end, 6),
            "machine_transcript_overlap": cue_text,
            "status": "pending agent semantic and frame-by-frame animation audit",
            "required_audit": ["presenter/evidence/UI distinction", "animation objects and layers",
                               "native keyframe/curve/mask timings", "native RGB region palette",
                               "font/layout/occlusion", "meaning and reusable parameters"]})
    atomic_json(output / "semantic-segments.json", semantic_segments)
    atomic_json(output / "scene-candidates.json", cut_candidates)
    summary = {
        "version": VERSION, "status": "complete", "identity": identity,
        "rank": job["rank"], "source": str(source), "source_bytes": source.stat().st_size,
        "source_sha256": source_hash, "processed_frames": frame_count,
        "container_declared_frames": declared_frames, "dimensions": sorted(dimensions),
        "first_pts_seconds": first_time, "last_pts_seconds": last_time,
        "estimated_final_frame_end_seconds": source_end,
        "native_frame_dt": {"minimum": float(intervals.min()) if len(intervals) else None,
                            "median": mode_dt, "maximum": float(intervals.max()) if len(intervals) else None,
                            "unique_rounded_9dp": len(np.unique(np.round(intervals, 9)))},
        "pts_missing": pts_missing, "pts_non_increasing": pts_non_increasing,
        "native_rgb_pixels_measured": pixel_total,
        "overall_rgb_mean": np.round(sums_total.astype(float)/pixel_total, 6).tolist(),
        "overall_rgb_histogram_8x8x8_counts": hist_total.tolist(),
        "maximum_adjacent_frame_rgb_mad": maximum_frame_rgb_mad,
        "scene_candidate_count": len(cut_candidates), "transition_cluster_count": len(clusters),
        "semantic_segment_count": len(semantic_segments),
        "motion_peaks": [{"rgb_mad": round(mad, 6), "frame_no": number, "pts_seconds": seconds}
                         for mad, number, seconds in sorted(motion_peaks, reverse=True)],
        "evidence": evidence, "decoder_logs": logs,
        "ledger": "frames.jsonl.gz", "ledger_sha256": sha256(ledger),
        "ledger_bytes": ledger.stat().st_size, "transcript_basis": transcript_basis,
        "verification_scope": {
            "machine": "Every decoded frame at native dimensions and native PTS; exact integer pixel sums and quantized histogram counts",
            "agent_visual_review": "not performed by this script",
            "semantic_animation_analysis": "pending; scene candidates and transcript intervals are not animation understanding",
            "palette": "Decoded native RGB means and 32-code-value histogram ranges; not exact individual artwork swatches",
            "conversion": "PyAV/FFmpeg swscale conversion of source pixel format to RGB24; source color metadata retained in source-metadata.json",
            "not_proven": "100% original palette, motion grammar or pixel-identical reconstruction"},
        "runtime": {"pyav": av.__version__, "numpy": np.__version__,
                    "libav_versions": {name: list(version) for name, version in av.library_versions.items()},
                    "elapsed_seconds": round(time.monotonic()-started, 3)},
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(summary_path, summary)
    lines = [f"# 来源 {job['rank']:02d} 完整段落待审清单", "",
             f"机器已逐帧处理 {frame_count:,} 帧；Agent 尚未逐帧实看。",
             "以下区间完整覆盖原片，切点只是 RGB 差分候选或每 10 秒的审查分段。",
             "ASR 仅辅助定位，不能据此认定动画语法、配色或字体。", "",
             "| 区间（原生 PTS 秒） | 机器转写 | 待完成 |", "|---|---|---|"]
    for segment in semantic_segments:
        text = segment["machine_transcript_overlap"].replace("|", "／").replace("\n", " ")
        lines.append(f"| {segment['start']:.3f}–{segment['end']:.3f} | {text or '（无转写）'} | 图层、路径、曲线、遮罩、字体、原生区域 RGB 与语义 |")
    (output / "semantic-review.md").write_text("\n".join(lines) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--source", type=Path, help="One local complete video")
    inputs.add_argument("--manifest", type=Path, help="Study sources.json with source_path and rank")
    parser.add_argument("--root", type=Path, help="Root for relative source_path; defaults to manifest parent")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--grid", type=int, default=4)
    parser.add_argument("--evidence-frames", type=int, default=12)
    parser.add_argument("--ranks", help="Optional comma-separated manifest ranks")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.workers <= 8 or not 1 <= args.grid <= 8 or not 2 <= args.evidence_frames <= 60:
        parser.error("workers 1–8, grid 1–8, evidence-frames 2–60")
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    library, kernel_hash = build_kernel(args.out / ".kernel")
    if args.manifest:
        manifest = json.loads(args.manifest.read_text())
        root = (args.root or args.manifest.parent).resolve()
        sources = manifest["sources"]
        if args.ranks:
            ranks = {int(item) for item in args.ranks.split(",")}
            sources = [item for item in sources if int(item["rank"]) in ranks]
        jobs = [{"rank": int(item["rank"]), "source": str((root / item["source_path"]).resolve()),
                 "expected_sha256": item.get("source_sha256"),
                 "duration_hint": float(item.get("duration", 0))} for item in sources]
        # Start long files first so a long tutorial does not become the final
        # serial tail. Output ranks and the captured search order stay intact.
        jobs.sort(key=lambda job: job["duration_hint"], reverse=True)
    else:
        jobs = [{"rank": 1, "source": str(args.source.resolve())}]
    if not jobs:
        parser.error("No sources selected")
    for job in jobs:
        job.update({"output": str(args.out / f"{job['rank']:02d}"),
                    "kernel_library": library, "kernel_sha256": kernel_hash,
                    "grid": args.grid, "evidence_frames": args.evidence_frames,
                    "overwrite": args.overwrite})
    started = time.monotonic()
    results, errors = [], []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process_source, job): job for job in jobs}
        for future in concurrent.futures.as_completed(futures):
            job = futures[future]
            try:
                result = future.result()
                results.append(result)
                print(json.dumps({"rank": job["rank"], "status": "complete",
                                  "frames": result["processed_frames"],
                                  "elapsed_seconds": result["runtime"]["elapsed_seconds"],
                                  "cache_reused": result.get("cache_reused", False)}), flush=True)
            except Exception as error:
                errors.append({"rank": job["rank"], "error": str(error)})
                print(json.dumps(errors[-1]), flush=True)
            atomic_json(args.out / "batch-progress.json", {
                "complete_ranks": sorted(result["rank"] for result in results),
                "errors": errors, "requested_source_count": len(jobs)})
    results.sort(key=lambda result: result["rank"])
    report = {"status": "complete" if not errors and len(results) == len(jobs) else "incomplete",
              "source_count": len(results), "requested_source_count": len(jobs),
              "processed_frames": sum(result["processed_frames"] for result in results),
              "source_bytes": sum(result["source_bytes"] for result in results),
              "native_rgb_pixels_measured": sum(result["native_rgb_pixels_measured"] for result in results),
              "ledger_bytes": sum(result["ledger_bytes"] for result in results),
              "agent_visual_review": "Not performed by this script; separate timecoded audit required",
              "semantics": "Full-span candidate intervals awaiting agent review, not automatic semantic recognition",
              "elapsed_seconds": round(time.monotonic()-started, 3),
              "sources": [{"rank": result["rank"], "frames": result["processed_frames"],
                           "source_sha256": result["source_sha256"], "ledger_sha256": result["ledger_sha256"],
                           "inventory": f"{result['rank']:02d}/inventory.json"} for result in results],
              "errors": errors}
    atomic_json(args.out / "full-decode-report.json", report)
    print(json.dumps({k: v for k, v in report.items() if k not in ("sources", "errors")}), flush=True)
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
