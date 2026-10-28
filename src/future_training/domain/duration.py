"""Contract 12 integer scheduling arithmetic, not an exercise safety assessment."""

from collections.abc import Sequence
from types import MappingProxyType

from future_training.schemas import Block, RepetitionBlock

DURATION_VERSION = "duration-v1"
# preset: (warm-up seconds, cooldown seconds, target seconds)
PRESETS = MappingProxyType({20: (180, 120, 1200), 30: (240, 180, 1800), 45: (300, 240, 2700)})
TOLERANCE_SECONDS = 60
TRANSITION_SECONDS = 45
SECONDS_PER_REPETITION = 4


def preset_timing(preset: int) -> tuple[int, int, int]:
    if type(preset) is not int or preset not in PRESETS:
        raise ValueError("unsupported duration preset")
    return PRESETS[preset]


def block_seconds(block: Block) -> int:
    work = (
        block.repetitions_per_set * SECONDS_PER_REPETITION
        if isinstance(block, RepetitionBlock)
        else block.work_seconds_per_set
    )
    return block.sets * work + (block.sets - 1) * block.rest_between_sets_seconds


def session_seconds(blocks: Sequence[Block], preset: int) -> int:
    warmup, cooldown, _ = preset_timing(preset)
    if not 3 <= len(blocks) <= 6:
        raise ValueError("session requires three to six blocks")
    return (
        warmup
        + cooldown
        + sum(block_seconds(block) for block in blocks)
        + TRANSITION_SECONDS * (len(blocks) - 1)
    )


def within_preset(seconds: int, preset: int) -> bool:
    target = preset_timing(preset)[2]
    return (
        type(seconds) is int and target - TOLERANCE_SECONDS <= seconds <= target + TOLERANCE_SECONDS
    )
