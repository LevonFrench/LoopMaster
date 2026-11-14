"""seconds_total conditioning must be a whole number of seconds.

Training conditions on math.ceil(n_samples / sample_rate), so a fractional
value is out of distribution and the DiT diverges into full-scale noise
(upstream Stability-AI/stable-audio-3#124). These tests need no model weights.
"""

import pytest

from stable_audio_3 import StableAudioModel

build = StableAudioModel._build_conditioning_dicts


@pytest.mark.parametrize(
    "duration, expected",
    [(1.2, 2), (1.5, 2), (0.5, 1), (0.8, 1), (1.0, 1), (2, 2), (380, 380), (2.0001, 3)],
)
def test_fractional_duration_rounds_up(duration, expected):
    cond, neg = build("a soft glass bell chime", None, duration, 1)
    assert cond == [{"prompt": "a soft glass bell chime", "seconds_total": expected}]
    assert neg is None


def test_negative_prompt_and_batch_lists_round_up():
    cond, neg = build(["a", "b"], ["x", "y"], [0.7, 3.0], 2)
    assert [c["seconds_total"] for c in cond] == [1, 3]
    assert [c["seconds_total"] for c in neg] == [1, 3]
    assert all(isinstance(c["seconds_total"], int) for c in cond + neg)
