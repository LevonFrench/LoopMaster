"""Download the Stable Audio 3 weights LoopMaster needs.

LoopMaster runs offline: the server only reads weights that are already on
disk under <repo>/models/huggingface. This script puts them there.

    python scripts/download_models.py medium
    python scripts/download_models.py small-music small-sfx
    python scripts/download_models.py --check medium     (no network; report only)

Set LOOPMASTER_MODEL_CACHE to keep the weights somewhere else. Use the same
value when you start the server.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_CACHE = Path(os.environ.get("LOOPMASTER_MODEL_CACHE") or ROOT / "models").resolve()

# The server sets HF_HOME to <cache>/huggingface, so its hub cache is the
# folder below. Only the cache location is set here, which leaves your normal
# Hugging Face login (or HF_TOKEN) in use for gated repositories.
os.environ["HF_HUB_CACHE"] = str(MODEL_CACHE / "huggingface" / "hub")

LAUNCHER_MODELS = ("medium", "small-music", "small-sfx", "medium-bf16")


def load_registry():
    """Load stable_audio_3/model_configs.py by path, without importing torch."""
    path = ROOT / "stable-audio-3" / "stable_audio_3" / "model_configs.py"
    spec = importlib.util.spec_from_file_location("loopmaster_sa3_model_configs", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def conditioner_folders(config_path: str) -> list[tuple[str, str]]:
    """Return (repo_id, subfolder) for each text encoder the model config names."""
    with open(config_path, encoding="utf-8") as handle:
        config = json.load(handle)
    found = []
    for entry in config.get("model", {}).get("conditioning", {}).get("configs", []):
        settings = entry.get("config", {})
        repo_id, subfolder = settings.get("repo_id"), settings.get("subfolder")
        if repo_id and subfolder and (repo_id, subfolder) not in found:
            found.append((repo_id, subfolder))
    return found


def cached_conditioner(repo_id: str, subfolder: str) -> Path | None:
    from huggingface_hub import snapshot_download
    from huggingface_hub.errors import LocalEntryNotFoundError

    try:
        snapshot = snapshot_download(repo_id, local_files_only=True)
    except (LocalEntryNotFoundError, OSError):
        return None
    folder = Path(snapshot) / subfolder
    has_config = (folder / "config.json").is_file()
    has_weights = any(folder.glob("*.safetensors")) or any(folder.glob("*.bin"))
    return folder if has_config and has_weights else None


def check(registry, alias: str) -> bool:
    model = registry.models[alias]
    config_repo = model.config_repo_id or model.repo_id
    config = registry._find_local_config(config_repo, model.repo_id, model.config_path)
    checkpoint = registry._find_local_file(model.repo_id, model.ckpt_path)
    print(f"  config:     {config or 'MISSING'}")
    print(f"  checkpoint: {checkpoint or 'MISSING'}")
    complete = bool(config and checkpoint)
    if config:
        for repo_id, subfolder in conditioner_folders(config):
            folder = cached_conditioner(repo_id, subfolder)
            print(f"  text encoder ({repo_id}/{subfolder}): {folder or 'MISSING'}")
            complete = complete and folder is not None
    return complete


def download(registry, alias: str) -> None:
    from huggingface_hub import snapshot_download

    model = registry.models[alias]
    config_path, _ = model.resolve()
    for repo_id, subfolder in conditioner_folders(config_path):
        print(f"  Fetching text encoder {repo_id}/{subfolder}")
        snapshot_download(repo_id, allow_patterns=[f"{subfolder}/*"])


def explain_access_error(error: Exception) -> str | None:
    from huggingface_hub.errors import GatedRepoError, HfHubHTTPError, RepositoryNotFoundError

    if isinstance(error, GatedRepoError):
        return "This model is gated on Hugging Face."
    if isinstance(error, RepositoryNotFoundError):
        return "Hugging Face did not show this repository to your account."
    if isinstance(error, HfHubHTTPError) and getattr(error.response, "status_code", None) in (401, 403):
        return "Hugging Face refused the download."
    return None


def main() -> int:
    registry = load_registry()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("models", nargs="+", choices=sorted(registry.models), metavar="MODEL",
                        help="one or more of: " + ", ".join(LAUNCHER_MODELS))
    parser.add_argument("--check", action="store_true", help="report what is on disk without downloading")
    args = parser.parse_args()

    if args.check:
        os.environ["HF_HUB_OFFLINE"] = "1"

    print(f"Model cache: {MODEL_CACHE}")
    failed = []
    for alias in args.models:
        repo_id = registry.models[alias].repo_id
        print(f"\n{alias} ({repo_id})")
        if args.check:
            if not check(registry, alias):
                failed.append(alias)
            continue
        try:
            download(registry, alias)
            print("  Ready.")
        except Exception as error:  # noqa: BLE001 - report every failure the same way
            failed.append(alias)
            reason = explain_access_error(error)
            if reason:
                print(f"  {reason}")
                print(f"  1. Open https://huggingface.co/{repo_id} and accept the license terms.")
                print("  2. Sign in on this machine:  stable-audio-3\\.venv\\Scripts\\hf.exe auth login")
                print("  3. Run this script again.")
            else:
                print(f"  Download failed: {error}")

    if failed:
        print("\nNot ready: " + ", ".join(failed))
        return 1
    print("\nAll requested models are on disk.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
