"""Offline-only H3 transport/state tests. No real account or media is accessed."""
import base64
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/autodl_h3_api.py"
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("autodl_h3_adapter_test", SCRIPT)
h3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h3)


class H3OfflineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "project"
        (self.project / "config").mkdir(parents=True)
        (self.project / "generation").mkdir()
        (self.project / "assets").mkdir()
        self.image = self.project / "assets/portrait.png"
        self.image.write_bytes(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aUe8AAAAASUVORK5CYII="))
        self.audio = self.project / "assets/guide.wav"
        with wave.open(str(self.audio), "wb") as source:
            source.setparams((1, 2, 16000, 16000, "NONE", "not compressed"))
            source.writeframes(b"\x00\x00" * 16000)
        self.cfg = {"resolution": "768p竖", "conservative_total_cap_cny": 40,
                    "api_key_env": "AUTODL_ART_OFFLINE_TEST_KEY"}
        self.plan = {"portrait": "assets/portrait.png", "presenter_description": "保持当前原创讲解者的形象。",
                     "presenter_review": {"status": "accepted", "portrait_sha256": h3.sha(self.image)},
                     "segments": [{"id": name, "guide_audio": "assets/guide.wav", "text": "这是示例文案。",
                                   "generation_seconds": 1, "seed": 7} for name in ("seg01", "seg02")]}
        self.billing = {"workflow_id": h3.WORKFLOW, "verified": True, "currency": "CNY",
                        "billing_basis": "generated_video_seconds", "unit_price_cny": 0.04,
                        "resolution": "768p竖"}
        self.write_config()

    def put(self, path, value):
        h3.save(self.project / path, value)

    def write_config(self):
        self.put("config/h3-provider.json", self.cfg)
        self.put("generation/segments.json", self.plan)
        self.put("config/autodl-billing-evidence.json", self.billing)

    def adapter(self):
        return h3.Adapter(self.project)

    def prepare(self, segment="seg01"):
        adapter = self.adapter()
        adapter.prepare(segment)
        return adapter

    def state(self, segment="seg01", **extra):
        manifest = h3.read_json(self.project / "generation" / segment / "input-manifest.json")
        state = {"id": segment, "status": "QUEUED", "task_id": "offline-task", "workflow_id": h3.WORKFLOW,
                 "request_sha256": manifest["request_sha256"], "reserved_cny": .04, **extra}
        self.put("generation/" + segment + "/task-state.json", state)
        return state

    @staticmethod
    def probe():
        return {"streams": [{"codec_type": "video", "nb_read_frames": "30"}, {"codec_type": "audio"}],
                "format": {"duration": "1.0"}}

    def accepted_preflight(self):
        adapter = self.prepare()
        raw = self.project / "generation/seg01/api-original.mp4"
        raw.write_bytes(b"offline mock raw video")
        state = self.state(status="DOWNLOADED", output="generation/seg01/api-original.mp4", output_sha256=h3.sha(raw))
        manifest = h3.read_json(self.project / "generation/seg01/input-manifest.json")
        self.put("generation/seg01/quality-acceptance.json", {"status": "accepted", "raw_output_sha256": h3.sha(raw),
                 **{k: manifest[k] for k in ("request_sha256", "portrait_sha256", "guide_audio_sha256")}})
        return adapter, state, raw

    def test_actual_cli_help_and_prepare_without_credential_read(self):
        self.cfg.pop("api_key_env")
        self.cfg["credentials_file"] = str(Path(self.temp.name) / "never-read-missing-secret.json")
        self.write_config()
        help_result = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
        prepared = subprocess.run([sys.executable, str(SCRIPT), "prepare", "seg01", "--project", str(self.project)],
                                  capture_output=True, text=True)
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        self.assertFalse(json.loads(prepared.stdout)["network_used"])
        body = h3.read_json(self.project / "generation/seg01/request.json")
        self.assertIn(self.plan["presenter_description"], body["prompt"])
        self.assertIn(self.plan["segments"][0]["text"], body["prompt"])
        self.assertNotIn("深蓝圆领毛衣", body["prompt"])
        self.assertFalse((self.project / "generation/seg01/task-state.json").exists())

    def test_prepare_cache_is_byte_stable_and_submitted_inputs_cannot_be_reprepared(self):
        adapter = self.prepare()
        run = self.project / "generation/seg01"
        before = {n: (h3.sha(run / n), (run / n).stat().st_mtime_ns) for n in ("request.json", "input-manifest.json")}
        adapter.prepare("seg01")
        self.assertEqual(before, {n: (h3.sha(run / n), (run / n).stat().st_mtime_ns) for n in before})
        self.state()
        with self.assertRaises(h3.H3Error):
            adapter.prepare("seg01")

    def test_unknown_post_retains_reservation_and_never_resubmits(self):
        for response in ({"code": "Success", "data": {}}, {"code": "Error", "data": {"task_id": "unconfirmed"}}):
            with self.subTest(response=response), tempfile.TemporaryDirectory() as alternate:
                # Use a fresh isolated project for each outcome.
                old = self.project
                shutil.copytree(old, Path(alternate) / "project")
                self.project = Path(alternate) / "project"
                adapter = self.prepare()
                with patch.object(adapter, "api", return_value=response) as api:
                    with self.assertRaises(h3.H3Error): adapter.submit("seg01")
                    state = h3.read_json(self.project / "generation/seg01/task-state.json")
                    self.assertEqual(state["status"], "SUBMISSION_UNCERTAIN")
                    self.assertEqual(state["reserved_cny"], .04)
                    with self.assertRaises(h3.H3Error): adapter.submit("seg01")
                    with self.assertRaises(h3.H3Error): adapter.resume("seg01")
                    self.assertEqual(api.call_count, 1)
                self.project = old

    def test_transport_interruption_does_not_enable_another_post(self):
        adapter = self.prepare()
        with patch.object(adapter, "api", side_effect=RuntimeError("mock timeout")) as api:
            with self.assertRaises(h3.H3Error): adapter.submit("seg01")
            with self.assertRaises(h3.H3Error): adapter.submit("seg01")
            self.assertEqual(api.call_count, 1)
        self.assertEqual(h3.read_json(self.project / "generation/seg01/task-state.json")["status"], "SUBMISSION_UNCERTAIN")

    def test_budget_and_quote_block_before_post(self):
        for key, value in (("conservative_total_cap_cny", .03), ("conservative_total_cap_cny", float("nan"))):
            self.cfg[key] = value
            self.write_config()
            adapter = self.prepare()
            with patch.object(adapter, "api") as api, self.assertRaises(h3.H3Error): adapter.submit("seg01")
            api.assert_not_called()
        self.cfg["conservative_total_cap_cny"] = 40
        self.billing["resolution"] = "480p竖"
        self.write_config()
        adapter = self.prepare()
        with patch.object(adapter, "api") as api, self.assertRaises(h3.H3Error): adapter.submit("seg01")
        api.assert_not_called()

    def test_uncertain_other_job_counts_against_budget(self):
        self.cfg["conservative_total_cap_cny"] = .06
        self.write_config()
        adapter = self.prepare()
        self.put("generation/other-attempt/task-state.json", {"status": "SUBMISSION_UNCERTAIN", "reserved_cny": .04})
        with patch.object(adapter, "api") as api, self.assertRaises(h3.H3Error): adapter.submit("seg01")
        api.assert_not_called()

    def test_legacy_task_only_resumes_get_and_preserves_request_bytes(self):
        adapter = self.prepare()
        self.state()  # Same legacy fields; no currency, no new private receipt required for a queued task.
        request_file = self.project / "generation/seg01/request.json"
        old = request_file.read_bytes()
        with patch.object(adapter, "api", return_value={"code": "Success", "data": {"status": "RUNNING", "duration": 123}}) as api:
            adapter.resume("seg01")
            api.assert_called_once_with("GET", "/api/v1/comfyui/comfyui_workflow/result/offline-task")
        self.assertEqual(request_file.read_bytes(), old)
        self.assertEqual(h3.read_json(self.project / "generation/seg01/task-state.json")["reserved_cny"], .04)

    def test_changed_current_input_blocks_existing_task_query(self):
        adapter = self.prepare()
        self.state()
        self.audio.write_bytes(self.audio.read_bytes() + b"changed")
        with patch.object(adapter, "api") as api, self.assertRaises(h3.H3Error): adapter.resume("seg01")
        api.assert_not_called()

    def test_representative_file_or_pending_record_is_not_acceptance(self):
        adapter, _, _ = self.accepted_preflight()
        adapter.prepare("seg02")
        review_path = self.project / "generation/seg01/quality-acceptance.json"
        review = h3.read_json(review_path)
        for field, bad in (("status", "pending"), ("raw_output_sha256", "0" * 64), ("portrait_sha256", "1" * 64)):
            wrong = {**review, field: bad}
            self.put("generation/seg01/quality-acceptance.json", wrong)
            with patch.object(adapter, "api") as api, patch.object(adapter, "verify_video", return_value=self.probe()), self.assertRaises(h3.H3Error):
                adapter.submit("seg02")
            api.assert_not_called()
        self.put("generation/seg01/quality-acceptance.json", review)
        with patch.object(adapter, "api", return_value={"code": "Success", "data": {"task_id": "second-offline-task"}}) as api, patch.object(adapter, "verify_video", return_value=self.probe()):
            result = adapter.submit("seg02")
        self.assertEqual(result["reserved_cny"], .04)
        api.assert_called_once()

    def test_downloaded_cache_requires_matching_raw_hash_and_decode(self):
        adapter, _, raw = self.accepted_preflight()
        with patch.object(adapter, "verify_video", return_value=self.probe()) as verify, patch.object(adapter, "api") as api:
            self.assertTrue(adapter.resume("seg01")["cache_used"])
            verify.assert_called_once_with(raw.resolve())
            api.assert_not_called()
        raw.write_bytes(b"tampered")
        with patch.object(adapter, "api") as api, self.assertRaises(h3.H3Error): adapter.resume("seg01")
        api.assert_not_called()

    def test_existing_unbound_video_is_never_adopted(self):
        adapter = self.prepare()
        self.state(status="SUCCESS")
        (self.project / "generation/seg01/api-original.mp4").write_bytes(b"unknown cached content")
        with patch.object(adapter, "api") as api, self.assertRaises(h3.H3Error): adapter.resume("seg01")
        api.assert_not_called()

    def test_successful_download_has_task_bound_receipt_and_private_state(self):
        adapter = self.prepare()
        self.state()
        response = {"code": "Success", "data": {"status": "SUCCESS", "results": [{"type": "video", "url": "https://cdn.example.test/output.mp4"}]}}
        def mock_download(url, path): path.write_bytes(b"mock original result")
        with patch.object(adapter, "api", return_value=response), patch.object(adapter, "download", side_effect=mock_download), patch.object(adapter, "verify_video", return_value=self.probe()):
            result = adapter.resume("seg01")
        self.assertEqual(result["status"], "DOWNLOADED")
        receipt = h3.read_json(self.project / "generation/seg01/download-manifest.json")
        state = h3.read_json(self.project / "generation/seg01/task-state.json")
        self.assertEqual(receipt["request_sha256"], state["request_sha256"])
        self.assertEqual(receipt["output_sha256"], state["output_sha256"])
        self.assertNotIn("task_id", result)

    def test_api_origin_redirect_and_output_url_guards(self):
        for origin in ("http://www.autodl.art", "https://www.autodl.art.evil.test", "https://key@www.autodl.art", "https://www.autodl.art/?token=bad"):
            with self.assertRaises(h3.H3Error): h3.api_origin(origin)
        for url in ("http://cdn.example.test/movie", "https://localhost/movie", "https://127.0.0.1/movie", "https://10.0.0.2/movie", "https://key@cdn.example.test/movie"):
            with self.assertRaises(h3.H3Error): h3.download_url(url)
        with self.assertRaises(h3.H3Error): h3.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.example.test")

    def test_explicit_api_env_uses_raw_authorization_and_redacts_responses(self):
        adapter = self.adapter()
        response = io.BytesIO(json.dumps({"code": "Success", "data": {"token": "offline-secret", "message": "echo offline-secret"}}).encode())
        with patch.dict(os.environ, {"AUTODL_ART_OFFLINE_TEST_KEY": "offline-secret", "FISH_API_KEY": "wrong-provider"}, clear=True), patch.object(h3.request, "build_opener") as build:
            build.return_value.open.return_value = response
            value = adapter.api("GET", "/api/v1/comfyui/comfyui_workflow/result/offline-task")
            req = build.return_value.open.call_args.args[0]
            self.assertEqual(req.get_header("Authorization"), "offline-secret")
            self.assertEqual(value["data"]["token"], "[redacted]")
            self.assertNotIn("offline-secret", json.dumps(value))
        with patch.dict(os.environ, {"FISH_API_KEY": "wrong-provider"}, clear=True), self.assertRaises(h3.H3Error): adapter.credentials()

    def test_private_credentials_file_host_and_explicit_keychain(self):
        secret = Path(self.temp.name) / "private-test-credential.json"
        secret.write_text(json.dumps({"base_url": "https://evil.example.test", "token": "offline-secret"}))
        secret.chmod(0o600)
        self.cfg.pop("api_key_env")
        self.cfg["credentials_file"] = str(secret)
        self.write_config()
        with self.assertRaises(h3.H3Error): self.adapter().credentials()
        self.cfg.pop("credentials_file")
        self.cfg["keychain"] = {"service": "AutoDL-Art-offline-tests", "account": "fake-account"}
        self.write_config()
        with patch("secret_store.lookup", return_value="offline-secret") as lookup:
            self.assertEqual(self.adapter().credentials()[1], "offline-secret")
            lookup.assert_called_once_with("AutoDL-Art-offline-tests", "fake-account")

    def test_output_symlink_hardlink_and_project_lock(self):
        adapter = self.prepare()
        self.state()
        output = self.project / "generation/seg01/api-original.mp4.part"
        before = h3.sha(self.image)
        output.symlink_to(self.image)
        with patch.object(adapter, "api") as api, self.assertRaises(h3.H3Error): adapter.resume("seg01")
        api.assert_not_called()
        output.unlink()
        os.link(self.project / "generation/seg01/request.json", output)
        with self.assertRaises(h3.H3Error): adapter.resume("seg01")
        output.unlink()
        os.link(self.image, output)
        with self.assertRaises(h3.H3Error): adapter.resume("seg01")
        self.assertEqual(h3.sha(self.image), before)
        output.unlink()
        with adapter.locked(), self.assertRaises(h3.H3Error): adapter.resume("seg01")

    def test_retry_plan_row_prompt_and_row_portrait_are_frozen(self):
        new_image = self.project / "assets/vertical.png"
        new_image.write_bytes(self.image.read_bytes())
        self.plan["preflight_id"] = "seg01"
        for row in self.plan["segments"]:
            row["portrait"] = "assets/vertical.png"
            row["prompt"] = "Use <Picture 1> and <Audio 1>. Locked dialogue: " + row["text"]
        self.write_config()
        adapter = self.prepare()
        body = h3.read_json(self.project / "generation/seg01/request.json")
        self.assertEqual(body["prompt"], self.plan["segments"][0]["prompt"])
        self.state()
        with patch.object(adapter, "api", return_value={"code": "Success", "data": {"status": "RUNNING"}}) as api:
            adapter.resume("seg01")
            api.assert_called_once()

    def test_default_prompt_separates_visual_description_and_quoted_dialogue(self):
        adapter = self.adapter()
        row = self.plan["segments"][0]
        prompt = adapter.prompt(row)
        self.assertIn("ONE continuous shot", prompt)
        self.assertIn("ZERO camera motion, zoom or cuts", prompt)
        self.assertIn("VISUAL DESCRIPTION ONLY (not spoken): " + json.dumps(self.plan["presenter_description"], ensure_ascii=False), prompt)
        self.assertTrue(prompt.endswith("\nSPOKEN DIALOGUE ONLY (Chinese): " + json.dumps(row["text"], ensure_ascii=False)))
        self.assertNotIn("嘴唇", prompt)
        self.assertNotIn("中近景", prompt)
        self.plan.pop("presenter_description")
        self.write_config()
        prompt = self.adapter().prompt(row)
        self.assertNotIn("VISUAL DESCRIPTION ONLY", prompt)
        self.assertNotIn("male", prompt)
        self.assertNotIn("sweater", prompt)
        row["text"] = '他说：“只讲一个重点。”'
        self.assertTrue(self.adapter().prompt(row).endswith(json.dumps(row["text"], ensure_ascii=False)))

    def test_description_and_explicit_prompt_changes_block_get(self):
        self.prepare()
        self.state()
        self.plan["presenter_description"] = "Changed camera and costume requirements."
        self.write_config()
        adapter = self.adapter()
        with patch.object(adapter, "api") as api, self.assertRaises(h3.H3Error):
            adapter.resume("seg01")
        api.assert_not_called()
        # Explicitly pinned prompts are exact identities, independent of default descriptions.
        frozen = h3.read_json(self.project / "generation/seg01/request.json")["prompt"]
        self.plan["segments"][0]["prompt"] = frozen
        self.write_config()
        adapter = self.adapter()
        with patch.object(adapter, "api", return_value={"code": "Success", "data": {"status": "RUNNING"}}) as api:
            adapter.resume("seg01")
        api.assert_called_once()
        self.plan["segments"][0]["prompt"] += " Additional camera instruction."
        self.write_config()
        adapter = self.adapter()
        with patch.object(adapter, "api") as api, self.assertRaises(h3.H3Error):
            adapter.resume("seg01")
        api.assert_not_called()

    def test_preflight_id_has_priority_over_legacy_alias(self):
        self.plan.update(preflight_id="seg02", representative_segment="seg01")
        self.write_config()
        self.assertEqual(self.adapter().representative, "seg02")

    def test_cdn_download_never_reads_or_forwards_api_credential(self):
        adapter = self.adapter()
        path = self.project / "assets/offline.part"
        with patch.object(adapter, "credentials", side_effect=AssertionError("must not read credential")), patch.object(h3.request, "build_opener") as build:
            build.return_value.open.return_value = io.BytesIO(b"offline bytes")
            adapter.download("https://cdn.example.test/output.mp4", path)
            req = build.return_value.open.call_args.args[0]
            self.assertIsNone(req.get_header("Authorization"))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "local FFmpeg required")
    def test_real_full_decode_of_synthetic_native_av(self):
        adapter = self.prepare()
        video = self.project / "assets/local-synthetic.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=navy:s=64x96:r=10:d=1",
                        "-i", str(self.audio), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-t", "1", str(video)], check=True)
        probe = adapter.verify_video(video)
        self.assertEqual(int(next(s for s in probe["streams"] if s["codec_type"] == "video")["nb_read_frames"]), 10)


if __name__ == "__main__":
    unittest.main()
