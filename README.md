# LoopMaster

A browser-based loop production studio powered by Stable Audio 3. Generate synchronized multi-track loops from text prompts, shape them with hardware-modeled FX, and export DAW-ready stems — all from one page. It runs on your own machine.

---

## What It Does

- **Text-to-Loop Generation** — Type a prompt, get four stereo loop variants at 44.1kHz. Drums, bass, leads, anything SA3 can produce.
- **Synchronized Grid** — Every track plays in lockstep. Add layers, audition variants, build arrangements in real time.
- **Channel Strip FX** — Each track gets a full effects chain: Luftikus EQ, Valentine saturation/compression, Ælapse tape delay & spring reverb, Scream distortion, and Filtr resonant filter. All hardware-modeled in Web Audio.
- **Remix Engine** — Use any variant as a seed for Variation, Inpainting, Continuation, or Call & Response regeneration.
- **Macro Controls** — One-knob sweeps for Space, Drive, Tone, Filter, and Crush. Musical results without tweaking individual parameters.
- **Master Limiter** — Brickwall limiter with makeup gain on the master bus. Loud and clean without clipping.
- **DAW Export** — Render the full mix to WAV (with FX and fade-out tail), or batch-export individual stems as a ZIP. All WAVs are ACIDized with tempo/key/beat markers for instant DAW import.

See [QUICKSTART.md](QUICKSTART.md) for a first session.

---

## Install

### Requirements

- Windows 10/11
- An NVIDIA GPU with CUDA for the Medium model (it fits a 12 GB card). The Small models also run on CPU, slowly.
- Python 3.10, 3.11 or 3.12 on PATH
- A free [Hugging Face](https://huggingface.co) account for the model weights
- Optional: [ffmpeg](https://ffmpeg.org) on PATH for MP3/OGG conversion, and [Node.js](https://nodejs.org) for desktop mode

### Setup

```bat
git clone https://github.com/LevonFrench/LoopMaster.git
cd LoopMaster
setup.bat
```

`setup.bat` creates a virtual environment in `stable-audio-3\.venv`, installs PyTorch (CUDA 12.6 build), Stable Audio 3 and the server, then offers to download a model. Use `setup.bat --cpu` for CPU-only PyTorch.

Model weights are not part of this repository. They download from Hugging Face into `models\` (about 5.5 GB for Medium). Stability AI asks you to accept its license before downloading, so if the download is refused:

1. Open the model page, for example [stable-audio-3-medium](https://huggingface.co/stabilityai/stable-audio-3-medium), and accept the terms.
2. Sign in on your machine: `stable-audio-3\.venv\Scripts\hf.exe auth login`
3. Run the download again:

```bat
stable-audio-3\.venv\Scripts\python.exe scripts\download_models.py medium
```

Other choices are `small-music`, `small-sfx` and `medium-bf16`. Add `--check` to see what is already on disk without downloading.

### Launch

```bat
run_normal.bat
```

A server window opens and asks which model to load. Once the model is ready, the app opens in your browser. To run the server alone, use `run_server.bat`, pick a model from the menu, and open [http://localhost:7861](http://localhost:7861).

The server makes no network requests for models: it only reads weights already on disk. It listens on `127.0.0.1` by default.

### Desktop mode (optional)

```bat
cd loopmaster-desktop
npm install
cd ..
run_desktop.bat
```

This opens LoopMaster in its own Electron window with a model launcher.

---

## Project Layout

```
LoopMaster/
├── loopmaster/
│   └── loopmaster-app/       # Flask backend + JS/CSS/HTML frontend
│       ├── app_server.py     # API server & generation worker
│       ├── static/           # Dashboard, skins, prompt catalogs
│       └── tests/            # Backend tests (tests_js/ holds the frontend tests)
├── loopmaster-desktop/       # Electron launcher
├── loopprompts/              # 50 ready-made loop pack prompt sheets
├── stable-audio-3/           # Stable Audio 3 library (modified copy of upstream)
├── scripts/
│   └── download_models.py    # Fetches model weights into models/
├── setup.bat                 # One-time install
├── run_normal.bat            # Start server + open browser
├── run_server.bat            # Server only (model selector)
└── run_desktop.bat           # Electron desktop mode
```

Generated audio is written to `loopmaster/loopmaster-app/outputs/`. Set `LOOPMASTER_OUTPUT_DIR` to write somewhere else, and `LOOPMASTER_MODEL_CACHE` to keep weights outside the repository folder.

---

## Loop Packs

[loopprompts/](loopprompts/README.md) holds 50 style packs. Each sheet lists BPM, key and four loop prompts you can paste into the prompt bar.

---

## Tests

```bat
stable-audio-3\.venv\Scripts\python.exe -m pip install pytest
cd loopmaster\loopmaster-app
..\..\stable-audio-3\.venv\Scripts\python.exe -m pytest tests
node --test tests_js/*.test.js
```

The backend tests do not load a model.

---

## License

LoopMaster is released under the [MIT License](LICENSE).

The `stable-audio-3/` folder is a modified copy of Stability AI's [stable-audio-3](https://github.com/Stability-AI/stable-audio-3) code, included under its own MIT license. **Model weights are separate**: they are downloaded from Hugging Face and governed by the [Stability AI Community License](https://stability.ai/license). Read it before commercial use. Details for every bundled component are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

---

## Credits

**Model**: [Stable Audio 3](https://stability.ai/) by Stability AI

**DSP References** (design inspiration; no code from these projects is included):
- [Luftikus EQ](https://github.com/lkjbdsp/lkjb-plugins/tree/master/Luftikus) — 6-band analog EQ
- [Valentine](https://github.com/tote-bag-labs/valentine) — Saturation & pumping compressor
- [Ælapse](https://github.com/smiarx/aelapse) — Tape delay & spring reverb
- [Scream](https://github.com/Cure-Audio/Scream) — Resonant distortion
- [Filtr](https://github.com/tiagolr/filtr) — Multi-type filter

**Libraries**: [tuna.js](https://github.com/Theodeus/tuna), [JSZip](https://stuk.github.io/jszip/), [html2canvas](https://html2canvas.hertzen.com)
