#!/usr/bin/env python3
"""Generate GPT Image 2.5 through the relay's Responses image tool."""
import argparse
import base64
import json
import mimetypes
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

p = argparse.ArgumentParser()
prompt_group = p.add_mutually_exclusive_group(required=True)
prompt_group.add_argument("--prompt")
prompt_group.add_argument("--prompt-file")
p.add_argument("--input-image", action="append", default=[])
p.add_argument("--output", required=True)
p.add_argument("--model", default="gpt-image-2.5-sunburst")
p.add_argument("--host-model", default=os.environ.get("IMAGE_HOST_MODEL", "gpt-5.6-sol"))
p.add_argument("--size", default="1024x1024")
p.add_argument("--quality", default="low", choices=["low", "medium", "high", "xhigh", "max", "auto"])
a = p.parse_args()
prompt = pathlib.Path(a.prompt_file).read_text(encoding="utf-8") if a.prompt_file else a.prompt
content = [{"type": "input_text", "text": prompt}]
for image_path in a.input_image:
    image_file = pathlib.Path(image_path)
    mime = mimetypes.guess_type(str(image_file))[0]
    if mime not in {"image/png", "image/jpeg", "image/webp"}:
        raise SystemExit("Input images must be PNG, JPEG or WebP")
    encoded = base64.b64encode(image_file.read_bytes()).decode("ascii")
    content.append({"type": "input_image", "image_url": f"data:{mime};base64,{encoded}", "detail": "high"})
if pathlib.Path(a.output).exists():
    raise SystemExit("Output already exists; choose a new versioned filename")

key = os.environ.get("IMAGE_API_KEY") or os.environ.get("OPENAI_API_KEY")
# GUI-launched apps may not pass launchd variables into a shell subprocess.
if not key and sys.platform == "darwin":
    for variable in ("IMAGE_API_KEY", "OPENAI_API_KEY"):
        try:
            key = subprocess.check_output(["/bin/launchctl", "getenv", variable], text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            key = None
        if key:
            break
if not key:
    raise SystemExit("IMAGE_API_KEY or OPENAI_API_KEY is not set")

base_url = os.environ.get("IMAGE_API_BASE_URL", "https://api.openai.com/v1").rstrip("/")
# Compatible providers can expose the requested image model through the same
# Responses image_generation shape. Keep provider routing in the environment,
# never in the skill package.
payload = {
    "model": a.host_model,
    "input": [{"role": "user", "content": content}],
    "tools": [{
        "type": "image_generation",
        "model": a.model,
        "action": "generate",
        "size": a.size,
        "quality": a.quality,
    }],
    "tool_choice": {"type": "image_generation"},
}
def request_image(payload):
    # A 524 is intermittent on this relay. Rotate the host model instead of
    # retrying the same overloaded route repeatedly.
    candidates = [
        (payload, payload["model"]),
    ]
    low_payload = json.loads(json.dumps(payload))
    low_payload["tools"][0]["quality"] = a.quality
    for host_model in ["gpt-5.6-luna", "gpt-5.6-sol"]:
        if host_model != payload["model"]:
            alternate = json.loads(json.dumps(low_payload))
            alternate["model"] = host_model
            candidates.append((alternate, host_model))

    last_detail = ""
    for attempt, (attempt_payload, host_model) in enumerate(candidates, 1):
        if attempt > 1:
            time.sleep(2)
            print(f"Relay HTTP 524; retrying with host model {host_model} (attempt {attempt}/{len(candidates)}).", file=sys.stderr)
        attempt_payload["stream"] = True
        body = json.dumps(attempt_payload).encode()
        req = urllib.request.Request(
            f"{base_url}/responses",
            data=body,
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as response:
                completed = None
                output_items = []
                for raw_line in response:
                    if not raw_line.startswith(b"data:"):
                        continue
                    text = raw_line[5:].strip()
                    if not text or text == b"[DONE]":
                        continue
                    event = json.loads(text)
                    if event.get("type") == "response.output_item.done":
                        item = event.get("item", {})
                        output_items.append(item)
                        if item.get("type") == "image_generation_call" and item.get("result"):
                            return {"output": [item]}
                    elif event.get("type") == "response.completed":
                        completed = event.get("response", {})
                if completed:
                    for item in completed.get("output", []):
                        if item.get("type") == "image_generation_call" and item.get("result"):
                            return {"output": [item]}
                raise RuntimeError("stream ended without a completed image_generation_call")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            if exc.code != 524:
                print(detail, file=sys.stderr)
                raise SystemExit(f"HTTP {exc.code}")
            last_detail = detail
            continue
    print(last_detail, file=sys.stderr)
    raise SystemExit("HTTP 524 after relay route rotation")

result = request_image(payload)

if result.get("error"):
    print(json.dumps(result["error"], ensure_ascii=False), file=sys.stderr)
    raise SystemExit("Image generation failed")

calls = [item for item in result.get("output", []) if item.get("type") == "image_generation_call"]
if not calls or calls[0].get("status") != "completed" or not calls[0].get("result"):
    raise SystemExit("Responses API did not return a completed image_generation_call")

out = pathlib.Path(a.output)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(base64.b64decode(calls[0]["result"]))
print(out)
