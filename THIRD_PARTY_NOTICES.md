# Third-party notices

LoopMaster's own code is released under the MIT License (see `LICENSE`). The repository also contains or depends on the work below.

## Included in this repository

| Component | Where | License |
|---|---|---|
| Stable Audio 3 inference library (modified copy of [Stability-AI/stable-audio-3](https://github.com/Stability-AI/stable-audio-3)) | `stable-audio-3/` | MIT, Copyright (c) 2026 Stability AI. See `stable-audio-3/LICENSE`. |
| tuna.js | `loopmaster/loopmaster-app/static/tuna.js` | MIT, Copyright (c) 2012 DinahMoe AB & Oskar Eriksson. License text is in the file header. |
| html2canvas 1.4.1 | `loopmaster/loopmaster-app/static/vendor/` | MIT. See `HTML2CANVAS-LICENSE` beside it. |
| JSZip 3.10.1 | `loopmaster/loopmaster-app/static/vendor/` | MIT or GPLv3, used here under MIT. See `JSZIP-LICENSE.markdown` beside it. |

The copy in `stable-audio-3/` differs from upstream: Windows install support, a local model lookup that works offline, memory and loading changes, and a fix that rounds fractional durations up before conditioning. `stable-audio-3/README.md` is upstream's README with local edits.

## Not included: model weights

No model weights ship with this repository. `setup.bat` and `scripts/download_models.py` download them from Hugging Face to your machine:

- `stabilityai/stable-audio-3-medium`, `stabilityai/stable-audio-3-small-music` and `stabilityai/stable-audio-3-small-sfx` are published by Stability AI under the [Stability AI Community License](https://stability.ai/license). Read it before any commercial use. The MIT license on this repository does not cover the weights or change their terms.
- Those repositories include a T5Gemma text encoder, which carries Google's Gemma terms.
- `dummy9996/stable-audio-3-bf16-comfyui` (the optional "Medium BF16" launcher choice) is a community conversion of the medium checkpoint, not an official Stability AI release.

## Design references

The channel-strip effects are named after open-source plugins that inspired their behaviour. LoopMaster implements them with Web Audio nodes and tuna.js and includes no source code from these projects:

- [Luftikus](https://github.com/lkjbdsp/lkjb-plugins/tree/master/Luftikus) (EQ)
- [Valentine](https://github.com/tote-bag-labs/valentine) (saturation and compression)
- [Ælapse](https://github.com/smiarx/aelapse) (tape delay and spring reverb)
- [Scream](https://github.com/Cure-Audio/Scream) (resonant distortion)
- [Filtr](https://github.com/tiagolr/filtr) (filter)

## Installed at setup time

`setup.bat` installs Python packages (PyTorch, torchaudio, transformers, huggingface-hub, Flask and others listed in `stable-audio-3/pyproject.toml` and `loopmaster/loopmaster-app/requirements.txt`) and, for desktop mode, `npm install` fetches Electron. Each is distributed under its own license by its own authors.
