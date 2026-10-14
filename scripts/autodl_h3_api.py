#!/usr/bin/env python3
"""Prepare, submit once, or resume AutoDL Art H3 segments in a private project."""
import argparse
import base64
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import uuid
from urllib import error, request
from urllib.parse import urlsplit
import wave

WORKFLOW = "minimax_h3_image_audio_to_video_v2_15s"
API_ORIGINS = {"https://www.autodl.art", "https://autodl.art"}
RESOLUTIONS = {"480p竖", "768p竖", "480p横", "768p横"}
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")


class H3Error(RuntimeError):
    """A deliberately credential-free, user-readable diagnostic."""


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def read_json(path):
    value = json.loads(Path(path).read_text())
    if not isinstance(value, dict):
        raise H3Error("Expected a JSON object")
    return value


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w") as output:
            json.dump(value, output, ensure_ascii=False, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        temporary.replace(path)
        os.chmod(path, 0o600)
    finally:
        if temporary.exists():
            temporary.unlink()


def number(value, name, positive=False):
    if isinstance(value, bool):
        raise H3Error(name + " must be a finite number")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise H3Error(name + " must be a finite number") from None
    if not result.is_finite() or result < 0 or (positive and result <= 0):
        raise H3Error(name + " must be a finite nonnegative number")
    return result


def api_origin(value):
    value = str(value).rstrip("/")
    if value not in API_ORIGINS:
        raise H3Error("Only approved HTTPS AutoDL Art API origins are allowed")
    return value


def download_url(value):
    parts = urlsplit(str(value))
    if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password
            or parts.port not in (None, 443) or parts.fragment):
        raise H3Error("Output must use HTTPS without user credentials or a nonstandard port")
    host = parts.hostname.lower().rstrip(".")
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise H3Error("Local output hosts are not permitted")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if "." not in host:
            raise H3Error("Output must have a public host") from None
    else:
        if not address.is_global:
            raise H3Error("Private output addresses are not permitted")
    return str(value)


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise H3Error("Redirect rejected; credentials and HTTPS scope are not forwarded")


def clean_response(value, key):
    if isinstance(value, dict):
        return {name: "[redacted]" if name.lower() in
                {"token", "api_key", "authorization", "secret", "access_token"}
                else clean_response(item, key) for name, item in value.items()}
    if isinstance(value, list):
        return [clean_response(item, key) for item in value]
    return value.replace(key, "[redacted]") if isinstance(value, str) and key else value


class Adapter:
    def __init__(self, project, config="config/h3-provider.json",
                 plan="generation/segments.json", billing="config/autodl-billing-evidence.json"):
        self.project = Path(project).resolve()
        if not self.project.is_dir():
            raise H3Error("Project directory does not exist")
        self.config_path = self.local(config)
        self.plan_path = self.local(plan)
        self.billing_path = self.local(billing)
        self.cfg, self.plan = read_json(self.config_path), read_json(self.plan_path)
        self.reject_embedded_keys(self.cfg)
        api_origin(self.cfg.get("base_url", "https://www.autodl.art"))
        if self.cfg.get("workflow_id", WORKFLOW) != WORKFLOW:
            raise H3Error("This adapter supports only the verified H3 v2 15-second workflow")
        if self.cfg.get("resolution") not in RESOLUTIONS:
            raise H3Error("Explicit supported resolution required")
        rows = self.plan.get("segments")
        if not isinstance(rows, list) or not rows:
            raise H3Error("Plan needs explicit segments")
        self.rows = {}
        for row in rows:
            name = row.get("id") if isinstance(row, dict) else None
            if not isinstance(name, str) or not IDENTIFIER.fullmatch(name) or name in self.rows:
                raise H3Error("Segment IDs must be unique safe identifiers")
            self.rows[name] = row
        self.generation = self.local("generation")
        self.representative = self.plan.get("preflight_id", self.plan.get("representative_segment", rows[0]["id"]))
        if self.representative not in self.rows:
            raise H3Error("Representative segment is not in the plan")

    @staticmethod
    def reject_embedded_keys(value):
        if isinstance(value, dict):
            for name, item in value.items():
                if name.lower() in {"token", "api_key", "authorization", "secret", "access_token"}:
                    raise H3Error("Profile may reference credentials, not contain them")
                Adapter.reject_embedded_keys(item)
        elif isinstance(value, list):
            for item in value:
                Adapter.reject_embedded_keys(item)

    def local(self, value):
        if not isinstance(value, (str, Path)) or not str(value):
            raise H3Error("Expected a project-relative path")
        path = (self.project / value).resolve()
        if not path.is_relative_to(self.project) or path == self.project:
            raise H3Error("Project path escapes its directory")
        return path

    @contextmanager
    def locked(self):
        self.generation.mkdir(parents=True, exist_ok=True)
        lock = self.local("generation/.autodl-h3.lock")
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise H3Error("Project is locked; reconcile a stopped process before removing its lock") from None
        os.close(descriptor)
        try:
            yield
        finally:
            lock.unlink()

    def paths(self, segment):
        if segment not in self.rows:
            raise H3Error("Segment is not in the plan")
        row = self.rows[segment]
        seconds, seed = row.get("generation_seconds"), row.get("seed")
        if isinstance(seconds, bool) or not isinstance(seconds, int) or not 1 <= seconds <= 15:
            raise H3Error("generation_seconds must be an integer from 1 to 15")
        if isinstance(seed, bool) or not isinstance(seed, int) or not isinstance(row.get("text"), str) or not row["text"].strip():
            raise H3Error("Segment needs an integer seed and locked nonempty text")
        run = self.local("generation/" + segment)
        image, audio = self.local(row.get("portrait", self.plan.get("portrait"))), self.local(row["guide_audio"])
        if any(p == run or p.is_relative_to(run) for p in (image, audio)):
            raise H3Error("Inputs cannot be stored in the mutable segment output directory")
        if image == audio:
            raise H3Error("Portrait and guide audio must be separate assets")
        protected = (image, audio, self.config_path, self.plan_path, self.billing_path)
        for name in ("request.json", "input-manifest.json", "task-state.json", "submit-response.json",
                     "latest-response.json", "api-original.mp4", "api-original.mp4.part",
                     "download-manifest.json", "output-probe.json", "quality-acceptance.json"):
            path = run / name
            if path.is_symlink() or path.resolve() in protected or (path.exists() and not path.is_file()):
                raise H3Error("Segment files must not link to or overwrite inputs/configuration")
            if path.exists() and any(p.exists() and os.path.samefile(path, p) for p in protected):
                raise H3Error("Segment output aliases a protected input")
            if path.exists() and path.stat().st_nlink != 1:
                raise H3Error("Mutable segment files must not be hard-linked")
        return row, run, image, audio

    def credentials(self):
        sources = [name for name in ("credentials_file", "api_key_env", "keychain") if self.cfg.get(name)]
        if len(sources) != 1:
            raise H3Error("Configure exactly one explicit AutoDL credential source")
        base = api_origin(self.cfg.get("base_url", "https://www.autodl.art"))
        if sources[0] == "credentials_file":
            path = Path(str(self.cfg["credentials_file"])).expanduser()
            if not path.is_absolute():
                path = self.project / path
            path = path.resolve()
            if not path.is_file() or (os.name != "nt" and stat.S_IMODE(path.stat().st_mode) & 0o077):
                raise H3Error("Credential file must be a private regular file (0600/0400)")
            secret = read_json(path)
            secret_base = api_origin(secret.get("base_url", base))
            if "base_url" in self.cfg and secret_base != base:
                raise H3Error("Credential and configured API origins disagree")
            base, key = secret_base, secret.get("token")
        elif sources[0] == "api_key_env":
            name = self.cfg["api_key_env"]
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                raise H3Error("Explicit environment variable name required")
            key = os.environ.get(name)
        else:
            settings = self.cfg["keychain"]
            if (not isinstance(settings, dict) or not settings.get("service")
                    or not settings.get("account")):
                raise H3Error("Explicit Keychain service and account required")
            from secret_store import lookup
            key = lookup(settings["service"], settings["account"])
        if not isinstance(key, str) or not key or any(char.isspace() for char in key):
            raise H3Error("Configured AutoDL API credential is unavailable or invalid")
        return base, key

    def api(self, method, path, payload=None):
        base, key = self.credentials()  # Only actual API requests read the credential.
        if not path.startswith("/api/v1/comfyui/comfyui_workflow/") or "?" in path or "#" in path:
            raise H3Error("API path is outside the documented workflow contract")
        req = request.Request(base + path, method=method,
                              data=json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None,
                              headers={"Authorization": key, "Content-Type": "application/json"})
        try:
            with request.build_opener(NoRedirect()).open(req, timeout=90) as response:
                result = json.load(response)
        except error.HTTPError as exc:
            raise H3Error("AutoDL API returned HTTP " + str(exc.code)) from None
        except Exception:
            raise H3Error("AutoDL API request did not yield a verified response") from None
        if not isinstance(result, dict):
            raise H3Error("AutoDL response must be a JSON object")
        return clean_response(result, key)

    def billing(self):
        value = read_json(self.billing_path)
        if (value.get("verified") is not True or value.get("billing_basis") != "generated_video_seconds"
                or value.get("currency") != "CNY" or value.get("workflow_id", WORKFLOW) != WORKFLOW):
            raise H3Error("Confirmed CNY generated-video-second billing is required")
        quote_resolution = value.get("resolution") or value.get("request_parameters_inspected", {}).get("resolution")
        if quote_resolution != self.cfg["resolution"]:
            raise H3Error("Billing quote resolution differs from this request")
        price = number(value.get("unit_price_cny"), "unit_price_cny", True)
        cap = number(self.cfg.get("conservative_total_cap_cny"), "conservative_total_cap_cny", True)
        return value, price, cap

    def prompt(self, row):
        text = row.get("text")
        if not isinstance(text, str) or not text.strip():
            raise H3Error("Locked segment text must be nonempty")
        if row.get("prompt") is not None:
            explicit = row["prompt"]
            if not isinstance(explicit, str) or not explicit.strip() or text not in explicit:
                raise H3Error("Explicit segment prompt must preserve its exact locked dialogue")
            return explicit
        description = self.plan.get("presenter_description", "")
        if not isinstance(description, str):
            raise H3Error("presenter_description must describe the current approved portrait")
        visual = ("\nVISUAL DESCRIPTION ONLY (not spoken): " + json.dumps(description, ensure_ascii=False)
                  if description.strip() else "")
        return ("Use the same presenter identity, clothing, background and composition as <Picture 1>. "
                "Keep the full head and shoulders visible at a fixed size. ONE continuous shot. "
                "ZERO camera motion, zoom or cuts. Follow <Audio 1> for voice and timing, "
                "with natural articulation and subtle blinking and breathing. "
                "No additional people, captions, music or dialogue. "
                "Visual instructions are not spoken." + visual +
                "\nSPOKEN DIALOGUE ONLY (Chinese): " + json.dumps(text, ensure_ascii=False))

    @staticmethod
    def media_bytes(path, kind):
        data = path.read_bytes()
        if kind == "image":
            if data.startswith(b"\x89PNG\r\n\x1a\n"):
                mime = "image/png"
            elif data.startswith(b"\xff\xd8\xff"):
                mime = "image/jpeg"
            elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
                mime = "image/webp"
            else:
                raise H3Error("Portrait must be an actual PNG, JPEG or WebP")
        elif data[:4] in (b"RIFF", b"RF64") and data[8:12] == b"WAVE":
            mime = "audio/wav"
        else:
            raise H3Error("Guide audio must be an actual WAV; normalize it locally before preparing")
        return data, mime

    def prepare(self, segment):
        with self.locked():
            row, run, image, audio = self.paths(segment)
            if (run / "task-state.json").exists():
                raise H3Error("Submitted segment must resume; prepare cannot replace its inputs")
            seconds = row.get("generation_seconds")
            if isinstance(seconds, bool) or not isinstance(seconds, int) or not 1 <= seconds <= 15:
                raise H3Error("generation_seconds must be an integer from 1 to 15")
            seed = row.get("seed")
            if isinstance(seed, bool) or not isinstance(seed, int):
                raise H3Error("Explicit integer seed required")
            image_data, image_mime = self.media_bytes(image, "image")
            audio_data, audio_mime = self.media_bytes(audio, "audio")
            with wave.open(str(audio)) as source:
                duration = source.getnframes() / source.getframerate()
            if duration <= 0 or duration > seconds + 0.001:
                raise H3Error("Guide audio would be empty or truncated by generation_seconds")
            body = {"prompt": self.prompt(row), "duration": seconds, "resolution": self.cfg["resolution"],
                    "seed": seed, "ref_image_0": "data:" + image_mime + ";base64," + base64.b64encode(image_data).decode(),
                    "ref_audio_0": "data:" + audio_mime + ";base64," + base64.b64encode(audio_data).decode()}
            request_file, manifest_path = run / "request.json", run / "input-manifest.json"
            if request_file.exists() and read_json(request_file) != body:
                raise H3Error("Prepared input changed; use a new segment/attempt directory")
            if not request_file.exists():
                save(request_file, body)
            identity = {"workflow_id": WORKFLOW, "portrait_sha256": sha(image),
                        "guide_audio_sha256": sha(audio), "text": row["text"], "seed": seed,
                        "duration_seconds": seconds, "resolution": self.cfg["resolution"],
                        "request_sha256": sha(request_file)}
            if manifest_path.exists():
                old = read_json(manifest_path)
                if any(old.get(key) != val for key, val in identity.items()):
                    raise H3Error("Prepared manifest identity changed")
            else:
                save(manifest_path, {**identity, "prepared_at": now(), "guide_duration_seconds": duration,
                                     "scope": "One accepted presenter master; local style variants reuse it"})
            return {"id": segment, "status": "PREPARED", "duration": seconds,
                    "request_sha256": identity["request_sha256"], "network_used": False}

    def inputs(self, segment, state=None):
        row, run, image, audio = self.paths(segment)
        manifest = read_json(run / "input-manifest.json")
        body = read_json(run / "request.json")
        expected = {"workflow_id": WORKFLOW, "portrait_sha256": sha(image), "guide_audio_sha256": sha(audio),
                    "request_sha256": sha(run / "request.json"), "text": row["text"],
                    "duration_seconds": row["generation_seconds"], "seed": row["seed"], "resolution": self.cfg["resolution"]}
        if any(manifest.get(key) != value for key, value in expected.items()):
            raise H3Error("Current input hashes/plan differ from the frozen request")
        if (type(body.get("duration")) is not int or type(body.get("seed")) is not int
                or body.get("duration") != row["generation_seconds"] or body.get("seed") != row["seed"]
                or body.get("resolution") != self.cfg["resolution"] or body.get("prompt") != self.prompt(row)):
            raise H3Error("Request does not match the locked segment")
        for field, file in (("ref_image_0", image), ("ref_audio_0", audio)):
            encoded = body.get(field, "")
            if not isinstance(encoded, str) or ";base64," not in encoded or not encoded.startswith("data:"):
                raise H3Error("Frozen request must embed the exact local input")
            try:
                raw = base64.b64decode(encoded.split(";base64,", 1)[1], validate=True)
            except ValueError:
                raise H3Error("Invalid frozen media encoding") from None
            if hashlib.sha256(raw).hexdigest() != sha(file):
                raise H3Error("Frozen media differs from current local input")
        if state and (state.get("id") != segment or state.get("workflow_id") != WORKFLOW
                      or state.get("request_sha256") != expected["request_sha256"]):
            raise H3Error("Task state belongs to another request/segment")
        return run, body, manifest

    def presenter_accepted(self, manifest):
        review = self.plan.get("presenter_review")
        if self.plan.get("presenter_review_file"):
            review = read_json(self.local(self.plan["presenter_review_file"]))
        if (not isinstance(review, dict) or review.get("status") != "accepted"
                or review.get("portrait_sha256") != manifest["portrait_sha256"]):
            raise H3Error("Submit requires an actually reviewed portrait accepted with its SHA")

    def verify_video(self, path):
        for program in ("ffmpeg", "ffprobe"):
            if not shutil.which(program):
                raise H3Error(program + " is required before submitting/downloading")
        decode = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"],
                                capture_output=True)
        if decode.returncode:
            raise H3Error("Full output decode failed; no output accepted")
        probe = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format",
                                "-of", "json", str(path)], capture_output=True, text=True)
        if probe.returncode:
            raise H3Error("Output probing failed")
        value = json.loads(probe.stdout)
        videos = [s for s in value.get("streams", []) if s.get("codec_type") == "video"]
        if (not videos or int(videos[0].get("nb_read_frames", 0)) <= 0
                or not any(s.get("codec_type") == "audio" for s in value.get("streams", []))):
            raise H3Error("Output requires fully decoded video frames and native audio")
        number(value["format"]["duration"], "native duration", True)
        return value

    def cached_output(self, segment, state):
        run, _, _ = self.inputs(segment, state)
        path = self.local(state.get("output", "generation/" + segment + "/api-original.mp4"))
        if path != run / "api-original.mp4" or not path.is_file() or sha(path) != state.get("output_sha256"):
            raise H3Error("Cached raw output missing/changed; do not regenerate automatically")
        self.verify_video(path)
        return path

    def preflight(self, candidate=None):
        run = self.local("generation/" + self.representative)
        state = read_json(run / "task-state.json")
        if state.get("status") != "DOWNLOADED" or not state.get("task_id"):
            raise H3Error("Representative raw output has not been downloaded")
        output = self.cached_output(self.representative, state)
        _, _, manifest = self.inputs(self.representative, state)
        review = read_json(run / "quality-acceptance.json")
        raw_hash = review.get("raw_output_sha256", review.get("output_sha256"))
        if review.get("status") != "accepted" or raw_hash != sha(output):
            raise H3Error("Representative raw preflight needs accepted status and exact output SHA")
        if review.get("output_sha256", raw_hash) != raw_hash:
            raise H3Error("Preflight contains contradictory raw output hashes")
        for key in ("portrait_sha256", "guide_audio_sha256"):
            if review.get(key) != manifest[key]:
                raise H3Error("Preflight acceptance does not bind the frozen input hashes")
        if review.get("request_sha256", manifest["request_sha256"]) != manifest["request_sha256"]:
            raise H3Error("Preflight request identity differs from its frozen task")
        if review.get("task_id", state["task_id"]) != state["task_id"]:
            raise H3Error("Preflight acceptance belongs to a different task")
        if candidate and candidate["portrait_sha256"] != manifest["portrait_sha256"]:
            raise H3Error("Remaining segments must use the accepted preflight's exact portrait")

    @staticmethod
    def summary(state, cached=False):
        return {key: state.get(key) for key in ("id", "status", "reserved_cny", "actual_fee_cny")} | {"cache_used": cached}

    def submit(self, segment):
        with self.locked():
            row, run, _, _ = self.paths(segment)
            state_path = run / "task-state.json"
            if state_path.exists():
                state = read_json(state_path)
                self.inputs(segment, state)
                if not state.get("task_id"):
                    raise H3Error("Existing submission has no ID; reconcile it, never blind POST again")
                if state.get("status") == "DOWNLOADED":
                    self.cached_output(segment, state)
                return self.summary(state, True)
            run, body, manifest = self.inputs(segment)
            if segment == self.representative:
                self.presenter_accepted(manifest)
            billing, price, cap = self.billing()
            reservation = number(body["duration"], "generation seconds", True) * price
            committed = Decimal(0)
            for path in self.generation.glob("*/task-state.json"):
                state = read_json(path)
                if state.get("currency", "CNY") != "CNY":
                    raise H3Error("Existing budget ledger has a different currency")
                if "reserved_cny" not in state:
                    raise H3Error("Existing task reservation is unknown; reconcile its project budget")
                committed += max(number(state["reserved_cny"], "reserved_cny"),
                                 number(state.get("actual_fee_cny") or 0, "actual_fee_cny"))
            if committed + reservation > cap:
                raise H3Error("Confirmed project CNY budget would be exceeded")
            if segment != self.representative:
                self.preflight(manifest)
            for program in ("ffmpeg", "ffprobe"):
                if not shutil.which(program):
                    raise H3Error(program + " is required before sending a paid request")
            state = {"id": segment, "status": "SUBMITTING", "task_id": None, "created_at": now(),
                     "workflow_id": WORKFLOW, "currency": "CNY", "reserved_cny": float(reservation),
                     "unit_price_cny": float(price), "billing_basis": billing["billing_basis"],
                     "actual_fee_cny": None, "request_sha256": manifest["request_sha256"]}
            save(state_path, state)
            try:
                response = self.api("POST", "/api/v1/comfyui/comfyui_workflow/" + WORKFLOW, body)
            except Exception:
                state.update(status="SUBMISSION_UNCERTAIN", updated_at=now())
                save(state_path, state)
                raise H3Error("Submission outcome uncertain; keep reservation and reconcile the task ID") from None
            save(run / "submit-response.json", response)
            data = response.get("data")
            task = data.get("task_id") if isinstance(data, dict) else None
            if response.get("code") != "Success" or not task or not IDENTIFIER.fullmatch(str(task)):
                state.update(status="SUBMISSION_UNCERTAIN", api_code=response.get("code"), updated_at=now())
                save(state_path, state)
                raise H3Error("No trustworthy task ID; no automatic resubmission or reservation release")
            state.update(task_id=task, status=str(data.get("status", "QUEUED")).upper(),
                         api_code=response.get("code"), updated_at=now())
            save(state_path, state)
            self.inputs(segment, state)
            return self.summary(state)

    def download(self, url, path):
        # Separate request object: never reuse the authenticated API opener/headers.
        req = request.Request(download_url(url), method="GET")
        if path.is_symlink() or (path.exists() and (not path.is_file() or path.stat().st_nlink != 1)):
            raise H3Error("Partial download cannot alias another file")
        if path.exists():
            path.replace(path.with_name(path.name + ".interrupted-" + uuid.uuid4().hex[:8]))
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
        try:
            with os.fdopen(descriptor, "wb") as output, request.build_opener(NoRedirect()).open(req, timeout=90) as response:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    output.write(chunk)
        except Exception:
            raise H3Error("Output download interrupted; resume the same task without POST") from None
        os.chmod(path, 0o600)

    def resume(self, segment):
        with self.locked():
            _, run, _, _ = self.paths(segment)
            state_path = run / "task-state.json"
            state = read_json(state_path)
            self.inputs(segment, state)
            if state.get("status") == "DOWNLOADED":
                self.cached_output(segment, state)
                return self.summary(state, True)
            task = state.get("task_id")
            if not task or not IDENTIFIER.fullmatch(str(task)):
                raise H3Error("No trustworthy task ID; reconcile the existing submission, never blind retry")
            output, part = run / "api-original.mp4", run / "api-original.mp4.part"
            receipt_path = run / "download-manifest.json"
            if output.exists():
                if not receipt_path.exists():
                    raise H3Error("Existing raw file has no task-bound receipt; do not adopt an unknown cache")
                receipt = read_json(receipt_path)
                if (receipt.get("task_id") != task or receipt.get("request_sha256") != state["request_sha256"]
                        or receipt.get("output_sha256") != sha(output)):
                    raise H3Error("Raw download receipt identity mismatch")
                self.verify_video(output)
                state.update(status="DOWNLOADED", output=str(output.relative_to(self.project)),
                             output_sha256=receipt["output_sha256"], updated_at=now())
                save(state_path, state)
                return self.summary(state, True)
            response = self.api("GET", "/api/v1/comfyui/comfyui_workflow/result/" + str(task))
            save(run / "latest-response.json", response)
            if response.get("code") != "Success" or not isinstance(response.get("data"), dict):
                raise H3Error("Provider query did not return Success; existing task is preserved")
            data = response["data"]
            state.update(status=str(data.get("status", "UNKNOWN")).upper(), updated_at=now(),
                         provider_processing_seconds=data.get("duration"))
            for key in ("cost", "fee", "amount"):
                if key in data:
                    state["provider_" + key] = data[key]  # Unknown units; never convert to actual_fee_cny.
            save(state_path, state)
            if state["status"] not in ("SUCCESS", "COMPLETED"):
                return self.summary(state)
            videos = [item for item in data.get("results", []) if isinstance(item, dict)
                      and (item.get("type") == "video" or item.get("file_type") == "mp4")]
            if not videos or not videos[0].get("url"):
                raise H3Error("Success response has no downloadable video")
            url = download_url(videos[0]["url"])
            self.paths(segment)
            self.download(url, part)
            probe = self.verify_video(part)
            self.inputs(segment, state)
            receipt = {"task_id": task, "request_sha256": state["request_sha256"],
                       "output_sha256": sha(part), "full_decode": "passed", "downloaded_at": now()}
            save(receipt_path, receipt)
            save(run / "output-probe.json", probe)
            part.replace(output)
            state.update(status="DOWNLOADED", output=str(output.relative_to(self.project)),
                         output_sha256=receipt["output_sha256"], updated_at=now())
            save(state_path, state)
            return self.summary(state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "submit", "resume"])
    parser.add_argument("segment", help="Segment ID declared in generation/segments.json")
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--config", default="config/h3-provider.json", help="Project-relative configuration")
    parser.add_argument("--plan", default="generation/segments.json", help="Project-relative segment plan")
    parser.add_argument("--billing", default="config/autodl-billing-evidence.json", help="Project-relative verified billing")
    args = parser.parse_args()
    try:
        adapter = Adapter(args.project, args.config, args.plan, args.billing)
        result = getattr(adapter, args.action)(args.segment)
        print(json.dumps(result, ensure_ascii=False))
    except H3Error as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (RuntimeError, ValueError, OSError, KeyError, TypeError, wave.Error):
        # Public CLI never prints raw provider errors, payloads, paths to secrets, or token values.
        print("AutoDL operation failed; inspect private project state/configuration. No automatic paid retry.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
