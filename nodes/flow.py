"""
Jovimetrix - http://www.github.com/amorano/jovimetrix
Logic and Code flow nodes
"""

import os
import time
from enum import Enum
from typing import Any

from loguru import logger

import comfy
from server import PromptServer
import nodes

from Jovimetrix import ComfyAPIMessage, JOVBaseNode, \
    IT_REQUIRED, IT_FLIP, WILDCARD, TimedOutException
from Jovimetrix.sup.lexicon import Lexicon
from Jovimetrix.sup.util import deep_merge_dict, zip_longest_fill, convert_parameter

# min amount of time before showing the cancel dialog
JOV_DELAY_MIN = 1
try: JOV_DELAY_MIN = int(os.getenv("JOV_DELAY_MIN", JOV_DELAY_MIN))
except: pass
JOV_DELAY_MIN = max(1, JOV_DELAY_MIN)

# max 10 minutes to start
JOVI_DELAY_MAX = 600
try: JOVI_DELAY_MAX = int(os.getenv("JOVI_DELAY_MAX", JOVI_DELAY_MAX))
except: pass

# =============================================================================

class EnumComparison(Enum):
    EQUAL = 0
    NOT_EQUAL = 1
    LESS_THAN = 2
    LESS_THAN_EQUAL = 3
    GREATER_THAN = 4
    GREATER_THAN_EQUAL = 5
    # LOGIC
    # NOT = 10
    AND = 20
    NAND = 21
    OR = 22
    NOR = 23
    XOR = 24
    XNOR = 25
    # TYPE
    IS = 80
    IS_NOT = 81
    # GROUPS
    IN = 82
    NOT_IN = 83

class DelayNode(JOVBaseNode):
    NAME = "DELAY (JOV) ✋🏽"
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/FLOW"
    DESCRIPTION = "Delay traffic. Electrons on the data bus go round."
    RETURN_TYPES = (WILDCARD,)
    RETURN_NAMES = (Lexicon.ROUTE,)

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"optional": {
            Lexicon.PASS_IN: (WILDCARD, {"default": None}),
            Lexicon.WAIT: ("INT", {"step": 1, "default" : 0}),
            Lexicon.HOLD: ("BOOLEAN", {"default": False}),
        },
        "hidden": {
            "id": "UNIQUE_ID"
        }}
        return deep_merge_dict(IT_REQUIRED, d)

    @classmethod
    def IS_CHANGED(cls) -> float:
        return float("nan")

    @staticmethod
    def parse_q(id, delay: int, forced:bool=False)-> bool:
        step = 0
        pbar = comfy.utils.ProgressBar(delay)
        # if the delay is longer than X seconds, pop up the "cancel continue"
        if delay > JOV_DELAY_MIN or forced:
            PromptServer.instance.send_sync("jovi-delay-user", {"id": id, "timeout": delay})

        while (step := step + 1) <= delay:
            try:
                if delay > JOV_DELAY_MIN or forced:
                    data = ComfyAPIMessage.poll(id, timeout=1)
                    if data.get('cancel', False):
                        nodes.interrupt_processing(True)
                        logger.warning(f"render cancelled delay: {id}")
                    else:
                        logger.info(f"render continued delay: {id}")
                    return True
                else:
                    time.sleep(1)
                    raise TimedOutException()
            except TimedOutException as e:
                pbar.update_absolute(step)
            except Exception as e:
                logger.error(str(e))
                return True
        return False

    def __init__(self) -> None:
        self.__delay = 0

    def run(self, id, **kw) -> tuple[Any]:
        o = kw[Lexicon.PASS_IN]
        hold = kw[Lexicon.HOLD]
        delay = min(kw[Lexicon.WAIT], JOVI_DELAY_MAX)
        if hold:
            cancel = False
            while not cancel:
                loop_delay = delay
                if loop_delay == 0:
                    loop_delay = JOVI_DELAY_MAX
                cancel = DelayNode.parse_q(id, loop_delay, True)
                print(cancel)
            return (o, )

        if delay != self.__delay:
            self.__delay = delay
            self.__delay = max(0, min(self.__delay, JOVI_DELAY_MAX))

        loops = int(self.__delay)
        if (remainder := self.__delay - loops) > 0:
            time.sleep(remainder)

        if loops > 0:
            cancel = DelayNode.parse_q(id, loops)
        return (o,)

class ComparisonNode(JOVBaseNode):
    """Compare two inputs."""

    NAME = "COMPARISON (JOV) 🕵🏽"
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/FLOW"
    DESCRIPTION = "Compare two inputs"
    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = (Lexicon.BOOLEAN, )

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"optional": {
            Lexicon.IN_A: (WILDCARD, {"default": None}),
            Lexicon.COMPARE: (EnumComparison._member_names_, {"default": EnumComparison.EQUAL.name}),
            Lexicon.IN_B: (WILDCARD, {"default": None})
        }}
        return deep_merge_dict(IT_REQUIRED, d, IT_FLIP)

    def run(self, **kw) -> tuple[bool]:
        result = []
        A = kw[Lexicon.IN_A]
        B = kw[Lexicon.IN_B]
        flip = kw[Lexicon.FLIP]
        op = kw[Lexicon.COMPARE]
        params = [tuple(x) for x in zip_longest_fill(A, B, op, flip)]
        pbar = comfy.utils.ProgressBar(len(params))
        for idx, (a, b, op, flip) in enumerate(params):
            if type(a) == tuple and type(b) == tuple:
                if (short := len(a) - len(b)) > 0:
                    b = list(b) + [0] * short
            typ_a, val_a = convert_parameter(a)
            _, val_b = convert_parameter(b)
            if flip:
                a, b = b, a
            op = EnumComparison[op]
            match op:
                case EnumComparison.EQUAL:
                    val = [a == b for a, b in zip(val_a, val_b)]
                case EnumComparison.GREATER_THAN:
                    val = [a > b for a, b in zip(val_a, val_b)]
                case EnumComparison.GREATER_THAN_EQUAL:
                    val = [a >= b for a, b in zip(val_a, val_b)]
                case EnumComparison.LESS_THAN:
                    val = [a < b for a, b in zip(val_a, val_b)]
                case EnumComparison.LESS_THAN_EQUAL:
                    val = [a <= b for a, b in zip(val_a, val_b)]
                case EnumComparison.NOT_EQUAL:
                    val = [a != b for a, b in zip(val_a, val_b)]
                # LOGIC
                # case EnumBinaryOperation.NOT = 10
                case EnumComparison.AND:
                    val = [a and b for a, b in zip(val_a, val_b)]
                case EnumComparison.NAND:
                    val = [not(a and b) for a, b in zip(val_a, val_b)]
                case EnumComparison.OR:
                    val = [a or b for a, b in zip(val_a, val_b)]
                case EnumComparison.NOR:
                    val = [not(a or b) for a, b in zip(val_a, val_b)]
                # IDENTITY
                case EnumComparison.IS:
                    val = [a is b for a, b in zip(val_a, val_b)]
                case EnumComparison.IS_NOT:
                    val = [a is not b for a, b in zip(val_a, val_b)]
                # GROUP
                case EnumComparison.IN:
                    val = [a in val_b for a in val_a]
                case EnumComparison.NOT_IN:
                    val = [a not in val_b for a in val_a]

            val = [typ_a[i](v) for i, v in enumerate(val)]
            if len(val) == 1:
                result.append(val[0])
            else:
                result.append(tuple(val))
            # logger.debug("{} {}", result, val)
            pbar.update_absolute(idx)

        return (result, )

class IfThenElseNode(JOVBaseNode):
    NAME = "IF-THEN-ELSE (JOV) 🔀"
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/FLOW"
    DESCRIPTION = "IF <valid> then A else B"
    RETURN_TYPES = (WILDCARD,)
    RETURN_NAMES = (Lexicon.RESULT, )

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"optional": {
            Lexicon.TRUE: (WILDCARD, {"default": None}),
            Lexicon.FALSE: (WILDCARD, {"default": None}),
            Lexicon.CONDITION: ("BOOLEAN", {"default": False}),
        }}
        return deep_merge_dict(IT_REQUIRED, d)

    def run(self, **kw) -> tuple[bool]:
        o = kw[Lexicon.CONDITION]
        T = kw[Lexicon.TRUE]
        F = kw[Lexicon.FALSE]
        if T is None or F is None:
            return (None,)
        return (T if o else F,)

# HOW TO MAKE COMFY HAVE A MEMORY BETWEEN AUTO-Q?
class SetGetData:
    DATA = {}
    DEFAULT = '🔺🟩🔵'

class SetNode(JOVBaseNode):
    NAME = "SET (JOV) 🟰"
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/FLOW"
    DESCRIPTION = "Set a value"
    RETURN_TYPES = (WILDCARD,)
    RETURN_NAMES = (Lexicon.RESULT, )

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"optional": {
            Lexicon.SETGET: (["SET", "GET"], {"default": "SET"}),
            Lexicon.KEY: ("STRING", {"default": ""}),
            Lexicon.VALUE: (WILDCARD, {"default": None}),
        }}
        return deep_merge_dict(IT_REQUIRED, d)

    @classmethod
    def IS_CHANGED(cls, *arg, **kw) -> float:
        return float("nan")

    def run(self, **kw) -> tuple[bool]:
        setget = kw[Lexicon.SETGET]
        key = kw[Lexicon.KEY]
        val = kw.get(Lexicon.VALUE, None)
        if setget == "SET":
            SetGetData.DATA[key] = val
            return (val, )

        if SetGetData.DATA.get(key, SetGetData.DEFAULT) == SetGetData.DEFAULT:
            SetGetData.DATA[key] = val
        return (SetGetData.DATA[key], )

class GetNode(JOVBaseNode):
    NAME = "GET (JOV) 🟰"
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/FLOW"
    DESCRIPTION = "Get a value"
    RETURN_TYPES = (WILDCARD,)
    RETURN_NAMES = (Lexicon.RESULT, )

    # HOW TO MAKE COMFY HAVE A MEMORY BETWEEN AUTO-Q
    DATA = {}
    DEFAULT = '🔺🟩🔵'

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"optional": {
            Lexicon.SETGET: (["SET", "GET"], {"default": "SET"}),
            Lexicon.KEY: ("STRING", {"default": ""}),
            Lexicon.VALUE: (WILDCARD, {"default": None}),
        }}
        return deep_merge_dict(IT_REQUIRED, d)

    @classmethod
    def IS_CHANGED(cls, *arg, **kw) -> float:
        return float("nan")

    def run(self, **kw) -> tuple[bool]:
        setget = kw[Lexicon.SETGET]
        key = kw[Lexicon.KEY]
        val = kw.get(Lexicon.VALUE, None)
        if setget == "SET":
            SetGetData.DATA[key] = val
            return (val, )
        if SetGetData.DATA.get(key, SetGetData.DEFAULT) == SetGetData.DEFAULT:
            SetGetData.DATA[key] = val
        return (SetGetData.DATA[key], )
