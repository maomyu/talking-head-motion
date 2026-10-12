#!/usr/bin/env python3
"""Plan and generate Fish native API narration, preserving resumable local outputs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib import error, request
from datetime import datetime, timezone

from secret_store import resolve

ENDPOINT = "https://api.fish.audio/v1/tts"
PRICES = {"s2.1-pro-free": 0.0, "s2.1-pro": 15.0, "s2-pro": 15.0}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write_json(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def make_plan(profile, text):
    forbidden = {"api_key", "token", "authorization", "secret", "fish_api_key"}
    def inspect(value):
        if isinstance(value, dict):
            if forbidden.intersection(k.lower() for k in value):
                raise ValueError("Credentials must not be embedded in the profile")
            for item in value.values():
                inspect(item)
        elif isinstance(value, list):
            for item in value:
                inspect(item)
    inspect(profile)
    model = profile.get("model")
    if model not in PRICES:
        raise ValueError("Exact supported model required; unknown/missing Fish models can be billed")
    voice = profile.get("reference_id", "")
    if not re.fullmatch(r"[a-f0-9]{32}", voice):
        raise ValueError("Expected a public/preset Fish reference_id")
    if not text.strip():
        raise ValueError("Narration is empty")
    speed = profile.get("speed", 1.0)
    if not isinstance(speed, (int, float)) or not math.isfinite(speed) or not 0.5 <= speed <= 2:
        raise ValueError("Speed must be 0.5–2")
    body = {"text": text, "reference_id": voice, "format": "wav", "sample_rate": 44100,
            "temperature": 0.7, "top_p": 0.7, "chunk_length": 300,
            "normalize": True, "condition_on_previous_chunks": True, "latency": "normal",
            "prosody": {"speed": speed, "volume": 0, "normalize_loudness": True}}
    identity = json.dumps({"model": model, "body": body}, sort_keys=True, ensure_ascii=False).encode()
    return {"schema_version": 1, "endpoint": ENDPOINT, "model": model, "body": body,
            "text_sha256": digest(text.encode()), "utf8_bytes": len(text.encode()),
            "estimated_usd": len(text.encode()) * PRICES[model] / 1_000_000,
            "request_sha256": digest(identity), "price_checked": "2026-10-11"}


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("API redirect rejected; no credential forwarded")


def normalize_audio(directory, state):
    for program in ("ffmpeg", "ffprobe"):
        if not shutil.which(program):
            raise RuntimeError(f"{program} required before API generation")
    source = directory / "provider-original.wav"
    output = directory / "narration.wav"
    temporary = directory / "narration.partial.wav"
    if not output.exists():
        result = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source),
                                 "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(temporary)],
                                capture_output=True)
        if result.returncode:
            raise RuntimeError("Local audio normalization failed; original cached, do not regenerate")
        temporary.replace(output)
    result = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                             "-of", "json", str(output)], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("Audio probing failed; original cached")
    probe = json.loads(result.stdout)
    duration = float(probe["format"]["duration"])
    if not math.isfinite(duration) or duration <= 0:
        raise RuntimeError("Audio has no valid positive duration")
    decode = subprocess.run(["ffmpeg", "-v", "error", "-i", str(output), "-f", "null", "-"],
                            capture_output=True)
    if decode.returncode:
        raise RuntimeError("Full audio decode failed; original cached")
    write_json(directory / "audio-probe.json", probe)
    state.update(status="generated_needs_content_review", finished_at=now(),
                 duration_seconds=duration, original_sha256=digest(source.read_bytes()),
                 narration_sha256=digest(output.read_bytes()), output=str(output.resolve()),
                 verification={"full_decode": "passed", "speech_content": "pending", "listening": "pending"})
    write_json(directory / "api-run.json", state)
    return state


def generate(plan, profile, directory, submit=False, allow_paid=False, max_usd=None):
    directory.mkdir(parents=True, exist_ok=True)
    ledger = directory / "api-run.json"
    state = json.loads(ledger.read_text()) if ledger.exists() else None
    if state:
        if state["request_sha256"] != plan["request_sha256"]:
            raise ValueError("Output directory belongs to a different request; choose a new directory")
        if state["status"] == "generated_needs_content_review":
            for filename, field in [("provider-original.wav", "original_sha256"), ("narration.wav", "narration_sha256")]:
                path = directory / filename
                if not path.exists() or digest(path.read_bytes()) != state[field]:
                    raise RuntimeError("Cached output missing or changed; do not resubmit automatically")
            return {**state, "cache_used": True}
        if (directory / "provider-original.wav").exists():
            return normalize_audio(directory, state)
        raise RuntimeError("Previous submission incomplete/failed; inspect api-run.json before any new submission")
    if not submit:
        raise ValueError("Generation requires --submit; use plan for a no-network review")
    if plan["estimated_usd"] > 0:
        if not allow_paid or max_usd is None or not math.isfinite(max_usd) or plan["estimated_usd"] > max_usd:
            raise ValueError("Paid Fish model requires an explicit sufficient --allow-paid --max-usd budget")
    for program in ("ffmpeg", "ffprobe"):
        if not shutil.which(program):
            raise RuntimeError(f"Missing {program}; no request sent")
    key = resolve(profile)
    write_json(directory / "request.json", plan)
    (directory / "script.txt").write_text(plan["body"]["text"] + "\n")
    state = {"schema_version": 1, "provider": "fish-audio-native-api", "model": plan["model"],
             "voice_id": plan["body"]["reference_id"], "request_sha256": plan["request_sha256"],
             "text_sha256": plan["text_sha256"], "estimated_usd": plan["estimated_usd"],
             "status": "submission_started", "submitted_at": now(), "request_id": None}
    write_json(ledger, state)
    req = request.Request(ENDPOINT, data=json.dumps(plan["body"], ensure_ascii=False).encode(),
                          headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                                   "model": plan["model"]}, method="POST")
    temporary = directory / "provider-original.partial.wav"
    try:
        with request.build_opener(NoRedirect()).open(req, timeout=600) as response:
            state["request_id"] = response.headers.get("X-Request-ID")
            write_json(ledger, state)
            with temporary.open("xb") as file:
                shutil.copyfileobj(response, file)
        with temporary.open("rb") as file:
            signature = file.read(12)
        if signature[:4] not in (b"RIFF", b"RF64") or signature[8:12] != b"WAVE":
            raise RuntimeError("Response was not WAV audio; partial response retained privately")
        temporary.replace(directory / "provider-original.wav")
        state["status"] = "received_needs_normalization"
        write_json(ledger, state)
    except error.HTTPError as exc:
        state.update(status="http_error_no_automatic_retry", http_status=exc.code, updated_at=now())
        write_json(ledger, state)
        raise RuntimeError(f"Fish API returned HTTP {exc.code}; no automatic paid fallback or retry") from None
    except Exception:
        state.update(status="submission_outcome_uncertain", updated_at=now())
        write_json(ledger, state)
        raise RuntimeError("API submission interrupted; inspect cached state before considering resubmission") from None
    return normalize_audio(directory, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["plan", "generate"])
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--text", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--allow-paid", action="store_true")
    parser.add_argument("--max-usd", type=float)
    args = parser.parse_args()
    try:
        profile = json.loads(args.profile.read_text())
        plan = make_plan(profile, args.text.read_text().strip())
        if args.action == "plan":
            args.output.mkdir(parents=True, exist_ok=True)
            write_json(args.output / "fish-request-plan.json", plan)
            result = {"status": "planned_no_network", "model": plan["model"],
                      "utf8_bytes": plan["utf8_bytes"], "estimated_usd": plan["estimated_usd"],
                      "request_sha256": plan["request_sha256"]}
        else:
            result = generate(plan, profile, args.output, args.submit, args.allow_paid, args.max_usd)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (RuntimeError, ValueError, OSError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
