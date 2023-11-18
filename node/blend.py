"""
     ██  ██████  ██    ██ ██ ███    ███ ███████ ████████ ██████  ██ ██   ██ 
     ██ ██    ██ ██    ██ ██ ████  ████ ██         ██    ██   ██ ██  ██ ██  
     ██ ██    ██ ██    ██ ██ ██ ████ ██ █████      ██    ██████  ██   ███  
██   ██ ██    ██  ██  ██  ██ ██  ██  ██ ██         ██    ██   ██ ██  ██ ██ 
 █████   ██████    ████   ██ ██      ██ ███████    ██    ██   ██ ██ ██   ██ 

               Procedural & Compositing Image Manipulation Nodes
                    http://www.github.com/amorano/jovimetrix

@author: amorano
@title: Jovimetrix Composition Pack
@nickname: Jovimetrix
@description: Blending operations for image inputs.
"""

import numpy as np
from PIL import Image, ImageChops
from ..util import *

# =============================================================================
# === EXPORT ===
# =============================================================================

__all__ = ["BlendNode"]

# =============================================================================
# === COMPOSITING ===
# =============================================================================

OPS = {
    'LERP': Image.blend,
    'ADD': ImageChops.add,
    'MINIMUM': ImageChops.darker,
    'MAXIMUM': ImageChops.lighter,
    'MULTIPLY': ImageChops.multiply,
    'SOFT LIGHT': ImageChops.soft_light,
    'HARD LIGHT': ImageChops.hard_light,
    'OVERLAY': ImageChops.overlay,
    'SCREEN': ImageChops.screen,
    'SUBTRACT': ImageChops.subtract,
    'DIFFERENCE': ImageChops.difference,
    'LOGICAL AND': np.bitwise_and,
    'LOGICAL OR': np.bitwise_or,
    'LOGICAL XOR': np.bitwise_xor,
}
_OPS = list(OPS.keys())

def blend(maskA, maskB, alpha, func, modeA, modeB, width, height, invert):
    maskA = SCALEFIT(maskA, width, height, modeA)
    h, w, _ = maskA.shape
    # print('BLEND', func, w, h)

    maskB = SCALEFIT(maskB, width, height, modeB)
    h, w, _ = maskB.shape
    # print('BLEND', w, h)

    if (op := OPS.get(func, None)):
        alpha = min(max(alpha, 0.), 1.)
        if func == 'LERP':
            maskA = cv2pil(maskA)
            maskB = cv2pil(maskB)
            maskA = op(maskA, maskB, alpha)
            maskA = pil2cv(maskA)
        elif func.startswith("LOGICAL"):
            maskA = np.array(maskA)
            maskB = np.array(maskB)
            maskA = op(maskA, maskB)
            maskA = Image.fromarray(maskA)
            maskA = pil2cv(maskA)
        else:
            maskA = cv2pil(maskA)
            maskB = cv2pil(maskB)
            if func == 'MULTIPLY':
                maskB = maskB.point(lambda i: 255 - int(i * alpha))
            else:
                maskB = maskB.point(lambda i: int(i * alpha))
            maskA = pil2cv(op(maskA, maskB))

    # rebound to target width and height
    maskA = cv2.resize(maskA, (width, height))

    if invert:
        maskA = INVERT(maskA, invert)

    return maskA

class BlendNode:
    """
    """
    @classmethod
    def INPUT_TYPES(s):
        d = {"required": {
                    "imageA": ("IMAGE", ),
                    "imageB": ("IMAGE", ),
                    "alpha": ("FLOAT", {"default": 1., "min": 0., "max": 1., "step": 0.05}),
                },
                "optional": {
                    "func": (_OPS, {"default": "LERP"}),
                    "modeA": (["FIT", "CROP", "ASPECT"], {"default": "FIT"}),
                    "modeB": (["FIT", "CROP", "ASPECT"], {"default": "FIT"}),
            }}
        return deep_merge_dict(d, IT_WH, IT_INVERT)

    DESCRIPTION = "Takes 2 Image inputs and an apha and performs a linear blend (alpha) between both images based on the selected operations."
    CATEGORY = "JOVIMETRIX 🔺🟩🔵"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE", )
    OUTPUT_NODE = True
    FUNCTION = "run"

    def run(self, imageA: torch.tensor, imageB: torch.tensor, alpha: float, func, modeA, modeB, width, height, invert):
        imageA = tensor2cv(imageA)
        imageB = tensor2cv(imageB)
        imageA = blend(imageA, imageB, alpha, func, modeA, modeB, width, height, invert)
        # print(imageA.shape)
        return (cv2tensor(imageA),)

class BlendMaskNode:
    """
    Made specifically for Matisse
    """
    @classmethod
    def INPUT_TYPES(s):
        d = {"required": {
                    "maskA": ("MASK", ),
                    "maskB": ("MASK", ),
                    "alpha": ("FLOAT", {"default": 1., "min": 0., "max": 1., "step": 0.05}),
                },
                "optional": {
                    "func": (_OPS, {"default": "LERP"}),
                    "modeA": (["FIT", "CROP", "ASPECT"], {"default": "FIT"}),
                    "modeB": (["FIT", "CROP", "ASPECT"], {"default": "FIT"}),
            }}
        return deep_merge_dict(d, IT_WH, IT_INVERT)

    DESCRIPTION = "Takes 2 Image inputs and an apha and performs a linear blend (alpha) between both masks based on the selected operations."
    CATEGORY = "JOVIMETRIX 🔺🟩🔵"
    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("MASK", )
    OUTPUT_NODE = True
    FUNCTION = "run"

    def run(self, maskA: torch.tensor, maskB: torch.tensor, alpha: float, func, modeA, modeB, width, height, invert):
        maskA = tensor2cv(maskA)
        maskB = tensor2cv(maskB)
        maskA = blend(maskA, maskB, alpha, func, modeA, modeB, width, height, invert)
        return (cv2tensor(maskA),)

NODE_CLASS_MAPPINGS = {
    "⚗️ Blend Images (jov)": BlendNode,
    "🧪 Blend Masks (jov)": BlendMaskNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {k: k for k in NODE_CLASS_MAPPINGS}
