#!/usr/bin/env python3
"""Generate from reference images using a configured Responses image tool."""
import argparse
import base64
import json
import mimetypes
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

p = argparse.ArgumentParser()
prompt_group = p.add_mutually_exclusive_group(required=True)
prompt_group.add_argument("--prompt")
prompt_group.add_argument("--prompt-file")
p.add_argument("--input-image", action="append", default=[])
p.add_argument("--output", required=True)
p.add_argument("--model", default=os.environ.get("IMAGE_MODEL"))
p.add_argument("--host-model", default=os.environ.get("IMAGE_HOST_MODEL"))
p.add_argument("--size", default="auto")
p.add_argument("--quality", default="high", choices=["low", "medium", "high", "xhigh", "max", "auto"])
a = p.parse_args()
base_url = os.environ.get("IMAGE_API_BASE_URL", "").rstrip("/")
if not base_url or not a.host_model or not a.model:
    p.error("Set IMAGE_API_BASE_URL, IMAGE_HOST_MODEL and IMAGE_MODEL for your provider; --host-model and --model can override model settings")
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
    payload["stream"] = True
    req = urllib.request.Request(
        f"{base_url}/responses",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            for raw_line in response:
                if not raw_line.startswith(b"data:"):
                    continue
                event_data = raw_line[5:].strip()
                if not event_data or event_data == b"[DONE]":
                    continue
                event = json.loads(event_data)
                if event.get("type") == "response.output_item.done":
                    item = event.get("item", {})
                    if item.get("type") == "image_generation_call" and item.get("result"):
                        return {"output": [item]}
                elif event.get("type") == "response.completed":
                    return event.get("response", {})
                elif event.get("type") in {"error", "response.failed", "response.incomplete"}:
                    raise SystemExit("Image service did not complete the request; check the provider dashboard")
        raise SystemExit("Stream ended without a completed image; check the provider before retrying")
    except urllib.error.HTTPError as exc:
        # Provider error bodies may echo credentials or private input; omit them.
        raise SystemExit(f"HTTP {exc.code}; check endpoint, model access and quota. No automatic retry was made") from None
    except (urllib.error.URLError, TimeoutError):
        raise SystemExit("Image service connection failed; check the provider before retrying") from None

result = request_image(payload)

if result.get("error"):
    raise SystemExit("Image generation failed")

calls = [item for item in result.get("output", []) if item.get("type") == "image_generation_call"]
if not calls or calls[0].get("status") != "completed" or not calls[0].get("result"):
    raise SystemExit("Responses API did not return a completed image_generation_call")

out = pathlib.Path(a.output)
image_bytes = base64.b64decode(calls[0]["result"], validate=True)
if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
    raise SystemExit("Provider returned a non-PNG result; select PNG output on your service")
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("xb") as output_file:
    output_file.write(image_bytes)
print(out)
