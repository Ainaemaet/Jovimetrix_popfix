"""
     ██  ██████  ██    ██ ██ ███    ███ ███████ ████████ ██████  ██ ██   ██ 
     ██ ██    ██ ██    ██ ██ ████  ████ ██         ██    ██   ██ ██  ██ ██  
     ██ ██    ██ ██    ██ ██ ██ ████ ██ █████      ██    ██████  ██   ███  
██   ██ ██    ██  ██  ██  ██ ██  ██  ██ ██         ██    ██   ██ ██  ██ ██ 
 █████   ██████    ████   ██ ██      ██ ███████    ██    ██   ██ ██ ██   ██ 

               Procedural & Compositing Image Manipulation Nodes
                    http://www.github.com/amorano/jovimetrix

                    Copyright 2023 Alexander Morano (Joviex)
"""

import os
import concurrent.futures
import time
from typing import Any

import cv2
import torch
import numpy as np
# import aiohttp.web
from PIL import Image, ImageFilter

from .sup.util import loginfo, logwarn, logerr
from .sup.stream import StreamingServer, StreamManager

try:
    from .sup import comp
except:
    import sup.comp as comp

# =============================================================================
# === CORE NODES ===
# =============================================================================

class JovimetrixBaseNode:
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {"required":{}}

    DESCRIPTION = "A Jovimetrix Node"
    CATEGORY = "JOVIMETRIX 🔺🟩🔵"
    RETURN_TYPES = ()
    OUTPUT_NODE = False
    # INPUT_IS_LIST = False
    FUNCTION = "run"

class JovimetrixBaseImageNode(JovimetrixBaseNode):
    RETURN_TYPES = ("IMAGE", "MASK",)
    RETURN_NAMES = ("image", "mask",)
    OUTPUT_NODE = True

# wildcard trick is 100% stolen from pythongossss's
class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False

WILDCARD = AnyType("*")

# =============================================================================
# === GLOBAL CONFIG ===
# =============================================================================

# auto-scan the camera ports on startup?
STREAMAUTOSCAN = os.getenv("JOVSTREAM_AUTO", '').lower() in ('true', '1', 't')
STREAMMANAGER = StreamManager(STREAMAUTOSCAN)

STREAMSERVER:StreamingServer = None
if (val := os.getenv("JOVSTREAM_SERVER", '').lower() in ('true', '1', 't')):
    STREAMSERVER = StreamingServer()

STREAMHOST = os.getenv("JOVSTREAM_HOST", '')
STREAMPORT = 7227
try: STREAMPORT = int(os.getenv("JOVSTREAM_PORT", STREAMPORT))
except: pass

# os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"

# =============================================================================
# === GLOBAL SUPPORTS ===
# =============================================================================

def deep_merge_dict(*dicts: dict) -> dict:
    """
    Deep merge multiple dictionaries recursively.
    """
    def _deep_merge(d1, d2):
        if not isinstance(d1, dict) or not isinstance(d2, dict):
            return d2

        merged_dict = d1.copy()

        for key in d2:
            if key in merged_dict:
                if isinstance(merged_dict[key], dict) and isinstance(d2[key], dict):
                    merged_dict[key] = _deep_merge(merged_dict[key], d2[key])
                elif isinstance(merged_dict[key], list) and isinstance(d2[key], list):
                    merged_dict[key].extend(d2[key])
                else:
                    merged_dict[key] = d2[key]
            else:
                merged_dict[key] = d2[key]
        return merged_dict

    merged = {}
    for d in dicts:
        merged = _deep_merge(merged, d)
    return merged

IT_REQUIRED = {
    "required": {}
}

IT_IMAGE = {
    "required": {
        "image": ("IMAGE", ),
    }}

IT_PIXELS = {
    "required": {
        "pixels": (WILDCARD, {"default": None}),
    }}

IT_PIXEL2 = {
    "required": {
        "pixelA": (WILDCARD, {"default": None}),
        "pixelB": (WILDCARD, {"default": None}),
    }}

IT_WH = {
    "optional": {
        "width": ("INT", {"default": 256, "min": 32, "max": 8192, "step": 1, "display": "number"}),
        "height": ("INT", {"default": 256, "min": 32, "max": 8192, "step": 1, "display": "number"}),
    }}

IT_WHMODE = {
    "optional": {
        "mode": (["NONE", "FIT", "CROP", "ASPECT"], {"default": "NONE"}),
    }}

IT_TRANS = {
    "optional": {
        "offsetX": ("FLOAT", {"default": 0., "min": -1., "max": 1., "step": 0.01, "display": "number"}),
        "offsetY": ("FLOAT", {"default": 0., "min": -1., "max": 1., "step": 0.01, "display": "number"}),
    }}

IT_ROT = {
    "optional": {
        "angle": ("FLOAT", {"default": 0., "min": -180., "max": 180., "step": 1., "display": "number"}),
    }}

IT_SCALE = {
    "optional": {
        "sizeX": ("FLOAT", {"default": 1., "min": 0.01, "max": 2., "step": 0.01, "display": "number"}),
        "sizeY": ("FLOAT", {"default": 1., "min": 0.01, "max": 2., "step": 0.01, "display": "number"}),
    }}

IT_TILE = {
    "optional": {
        "tileX": ("INT", {"default": 1, "min": 0, "step": 1, "display": "number"}),
        "tileY": ("INT", {"default": 1, "min": 0, "step": 1, "display": "number"}),
    }}

IT_EDGE = {
    "optional": {
        "edge": (["CLIP", "WRAP", "WRAPX", "WRAPY"], {"default": "CLIP"}),
    }}

IT_INVERT = {
    "optional": {
        "invert": ("FLOAT", {"default": 0., "min": 0., "max": 1., "step": 0.01}),
    }}

IT_COLOR = {
    "optional": {
        "R": ("FLOAT", {"default": 1., "min": 0., "max": 1., "step": 0.01, "display": "number"}),
        "G": ("FLOAT", {"default": 1., "min": 0., "max": 1., "step": 0.01, "display": "number"}),
        "B": ("FLOAT", {"default": 1., "min": 0., "max": 1., "step": 0.01, "display": "number"}),
    }}

IT_ORIENT = {
    "optional": {
        "orient": (["NORMAL", "FLIPX", "FLIPY", "FLIPXY"], {"default": "NORMAL"}),
    }}

IT_TRS = deep_merge_dict(IT_TRANS, IT_ROT, IT_SCALE)

IT_WHMODEI = deep_merge_dict(IT_WH, IT_WHMODE, IT_INVERT)

# =============================================================================
# === CREATION NODES ===
# =============================================================================

class ConstantNode(JovimetrixBaseImageNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return deep_merge_dict(IT_REQUIRED, IT_WH, IT_COLOR)

    DESCRIPTION = ""
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/CREATE"

    def run(self, width: int, height: int, R: float, G: float, B: float) -> tuple[torch.Tensor, torch.Tensor]:
        image = Image.new("RGB", (width, height), (int(R * 255.), int(G * 255.), int(B * 255.)) )
        return (comp.pil2tensor(image), comp.pil2tensor(image.convert("L")),)

class ShapeNode(JovimetrixBaseImageNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {
            "required": {
                "shape": (["CIRCLE", "SQUARE", "ELLIPSE", "RECTANGLE", "POLYGON"], {"default": "SQUARE"}),
                "sides": ("INT", {"default": 3, "min": 3, "max": 100, "step": 1}),
            },
        }
        return deep_merge_dict(d, IT_WH, IT_COLOR, IT_ROT, IT_SCALE, IT_INVERT)

    DESCRIPTION = ""
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/CREATE"

    def run(self, shape: str, sides: int, width: int, height: int, R: float, G: float, B: float,
            angle: float, sizeX: float, sizeY: float, invert: float) -> tuple[torch.Tensor, torch.Tensor]:

        image = None
        fill = (int(R * 255.),
                int(G * 255.),
                int(B * 255.),)

        match shape:
            case 'SQUARE':
                image = comp.sh_quad(width, height, sizeX, sizeX, fill=fill)

            case 'ELLIPSE':
                image = comp.sh_ellipse(width, height, sizeX, sizeY, fill=fill)

            case 'RECTANGLE':
                image = comp.sh_quad(width, height, sizeX, sizeY, fill=fill)

            case 'POLYGON':
                image = comp.sh_polygon(width, height, sizeX, sides, fill=fill)

            case _:
                image = comp.sh_ellipse(width, height, sizeX, sizeX, fill=fill)

        image = image.rotate(-angle)
        if invert > 0.:
            image = comp.pil2cv(image)
            image = comp.INVERT(image, invert)
            image = comp.cv2pil(image)

        return (comp.pil2tensor(image), comp.pil2tensor(image.convert("L")), )

class PixelShaderBaseNode(JovimetrixBaseImageNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"required": {},
            "optional": {
                "R": ("STRING", {"multiline": True, "default": "1. - np.minimum(1, np.sqrt((($u-0.5)**2 + ($v-0.5)**2) * 2))"}),
                "G": ("STRING", {"multiline": True}),
                "B": ("STRING", {"multiline": True}),
            },
        }
        if cls == PixelShaderImageNode:
            return deep_merge_dict(IT_IMAGE, d, IT_WH)
        return deep_merge_dict(d, IT_WH)

    CATEGORY = "JOVIMETRIX 🔺🟩🔵/CREATE"

    @staticmethod
    def shader(image: cv2.Mat, width: int, height: int, R: str, G: str, B: str) -> np.ndarray:
        import math
        from ast import literal_eval

        R = R.lower().strip()
        G = G.lower().strip()
        B = B.lower().strip()

        def parseChannel(chan, x, y) -> str:
            """
            x, y - current x,y position (output)
            u, v - tex-coord position (output)
            w, h - width/height (output)
            i    - value in original image at (x, y)
            """
            exp = chan.replace("$x", str(x))
            exp = exp.replace("$y", str(y))
            exp = exp.replace("$u", str(x/width))
            exp = exp.replace("$v", str(y/height))
            exp = exp.replace("$w", str(width))
            exp = exp.replace("$h", str(height))
            ir, ig, ib, = image[y, x]
            exp = exp.replace("$r", str(ir))
            exp = exp.replace("$g", str(ig))
            exp = exp.replace("$b", str(ib))
            return exp

        # Define the pixel shader function
        def pixel_shader(x, y):
            result = []
            for i, who in enumerate((B, G, R, )):
                if who == "":
                    result.append(image[y, x][i])
                    continue

                exp = parseChannel(who, x, y)
                try:
                    i = literal_eval(exp)
                    result.append(int(i * 255))
                except:
                    try:
                        i = eval(exp.replace("^", "**"))
                        result.append(int(i * 255))
                    except Exception as e:
                        logerr(str(e))
                        result.append(image[y, x][i])
                        continue

            return result

        # Create an empty numpy array to store the pixel values
        ret = np.zeros((height, width, 3), dtype=np.uint8)

        # Function to process a chunk in parallel
        def process_chunk(chunk_coords):
            y_start, y_end, x_start, x_end = chunk_coords
            for y in range(y_start, y_end):
                for x in range(x_start, x_end):
                    ret[y, x] = pixel_shader(x, y)

        # 12 seems to be the legit balance *for single node
        chunkX = chunkY = 8

        # Divide the image into chunks
        chunk_coords = []
        for y in range(0, height, chunkY):
            for x in range(0, width, chunkX):
                y_end = min(y + chunkY, height)
                x_end = min(x + chunkX, width)
                chunk_coords.append((y, y_end, x, x_end))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(process_chunk, chunk): chunk for chunk in chunk_coords}
            for _ in concurrent.futures.as_completed(futures):
                pass

        return ret

    def run(self, image: torch.tensor, width: int, height: int, R: str, G: str, B: str) -> tuple[torch.Tensor, torch.Tensor]:
        image = comp.tensor2cv(image)
        image = PixelShaderBaseNode.shader(image, width, height, R, G, B)
        return (comp.cv2tensor(image), comp.cv2mask(image), )

class PixelShaderNode(PixelShaderBaseNode):

    DESCRIPTION = ""

    def run(self, width: int, height: int, R: str, G: str, B: str) -> tuple[torch.Tensor, torch.Tensor]:
        image = torch.zeros((height, width, 3), dtype=torch.uint8)
        return super().run(image, width, height, R, G, B)

class PixelShaderImageNode(PixelShaderBaseNode):

    DESCRIPTION = ""

    def run(self, image: torch.tensor, width: int, height: int, R: str, G: str, B: str) -> tuple[torch.Tensor, torch.Tensor]:
        image = comp.tensor2cv(image)
        image = cv2.resize(image, (width, height))
        image = comp.cv2tensor(image)
        return super().run(image, width, height, R, G, B)

class WaveGeneratorNode(JovimetrixBaseNode):

    OP_WAVE = {
        "SINE": comp.wave_sine,
        "INV SINE": comp.wave_inv_sine,
        "ABS SINE": comp.wave_abs_sine,
        "COSINE": comp.wave_cosine,
        "INV COSINE": comp.wave_inv_cosine,
        "ABS COSINE": comp.wave_abs_cosine,
        "SAWTOOTH": comp.wave_sawtooth,
        "TRIANGLE": comp.wave_triangle,
        "RAMP": comp.wave_ramp,
        "STEP": comp.wave_step_function,
        "HAVER SINE": comp.wave_haversine,
        "NOISE": comp.wave_noise,
    }
    """
        "SQUARE": comp.wave_square,
        "PULSE": comp.wave_pulse,
        "EXP": comp.wave_exponential,
        "RECT PULSE": comp.wave_rectangular_pulse,

        "LOG": comp.wave_logarithmic,
        "GAUSSIAN": comp.wave_gaussian,
        "CHIRP": comp.wave_chirp_signal,
    }
    """

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"required":{
                "type": (list(WaveGeneratorNode.OP_WAVE.keys()), {"default": "SINE"}),
                "phase": ("FLOAT", {"default": 1.0, "min": 0.0, "step": 1.0}),
                "amp": ("FLOAT", {"default": 0.5, "min": 0.0, "step": 0.1}),
                "offset": ("FLOAT", {"default": 0.0, "min": 0.0, "step": 1.0}),
                "max": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 9999.0, "step": 0.05}),
                "frame": ("INT", {"default": 1.0, "min": 0.0, "step": 1.0}),
            }}
        return d

    DESCRIPTION = ""
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/CREATE"
    RETURN_TYPES = ("FLOAT", "INT", )

    def run(self, image: torch.tensor, width: int, height: int, R: str, G: str, B: str) -> tuple[torch.Tensor, torch.Tensor]:
        val = 0.

        return (val, int(val))

class GLSLNode(JovimetrixBaseImageNode):

    @classmethod
    def INPUT_TYPES(s) -> dict[str, dict]:
        return {
            "required": {
                "vertex": ("STRING", {"default": """
                                #version 330

                                in vec2 in_vert;
                                void main() {
                                    gl_Position = vec4(in_vert, 0.0, 1.0);
                                    }
                                """, "multiline": True}),
                "fragment": ("STRING", {"default": """
                                #version 330

                                out vec4 fragColor;
                                void main() {
                                    fragColor = vec4(1.0, 0.0, 0.0, 1.0); // Red color
                                }
                                """, "multiline": True}),
            }}

    DESCRIPTION = ""
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/**DO NOT USE**"

    def run(self, vertex: str, fragment: str) -> tuple[torch.Tensor, torch.Tensor]:
        import moderngl

        # @TODO: GET ACTUAL LITEGRAPH CONTEXT?
        ctx = moderngl.create_standalone_context(share=True)

        prog = ctx.program(vertex_shader=vertex, fragment_shader=fragment)

        # Create a simple quad
        vertices = np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype=np.float32)
        vbo = ctx.buffer(vertices)

        # Create a vertex array
        vao = ctx.simple_vertex_array(prog, vbo, 'in_vert')

        # Render the quad
        fbo = ctx.framebuffer(color_attachments=[ctx.texture((512, 512), 3)])
        fbo.use()
        vao.render(moderngl.TRIANGLE_STRIP)

        # Read the pixel data
        data = np.frombuffer(fbo.read(components=3, dtype='f1'), dtype=np.float32)
        data = np.nan_to_num(data * 255., nan=0.)
        data = np.clip(data, 0, 255).astype(np.uint8)
        image = Image.frombytes('RGB', fbo.size, fbo.read(), 'raw', 'RGB', 0, -1)
        return (comp.pil2tensor(image), comp.pil2mask(image))

# =============================================================================
# === TRANFORM NODES ===
# =============================================================================

class TransformNode(JovimetrixBaseImageNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return deep_merge_dict(IT_PIXELS, IT_TRS, IT_EDGE, IT_WH, IT_WHMODE)

    DESCRIPTION = "Translate, Rotate, Scale, Tile and Invert an input. All options allow for CROP or WRAPing of the edges."
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/TRANSFORM"

    def run(self, pixels: torch.tensor, offsetX: float, offsetY: float, angle: float, sizeX: float, sizeY: float,
            edge: str, width: int, height: int, mode: str) -> tuple[torch.Tensor, torch.Tensor]:

        pixels = comp.tensor2cv(pixels)
        pixels = comp.TRANSFORM(pixels, offsetX, offsetY, angle, sizeX, sizeY, edge, width, height, mode)
        return (comp.cv2tensor(pixels), comp.cv2mask(pixels), )

class TileNode(JovimetrixBaseImageNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return deep_merge_dict(IT_PIXELS, IT_TILE)

    DESCRIPTION = "Tile an Image with optional crop to original image size."
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/TRANSFORM"

    def run(self, pixels: torch.tensor, tileX: float, tileY: float) -> tuple[torch.Tensor, torch.Tensor]:
        pixels = comp.tensor2cv(pixels)
        height, width, _ = pixels.shape
        pixels = comp.EDGEWRAP(pixels, tileX, tileY)
        # rebound to target width and height
        pixels = cv2.resize(pixels, (width, height))
        return (comp.cv2tensor(pixels), comp.cv2mask(pixels), )

class MirrorNode(JovimetrixBaseImageNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"required": {
                "x": ("FLOAT", {"default": 0.5, "min": 0., "max": 1., "step": 0.01}),
                "y": ("FLOAT", {"default": 0.5, "min": 0., "max": 1., "step": 0.01}),
                "mode": (["X", "Y", "XY", "YX"], {"default": "X"}),
            },
        }
        return deep_merge_dict(IT_PIXELS, d, IT_INVERT)

    DESCRIPTION = "Flip an input across the X axis, the Y Axis or both, with independant centers."
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/TRANSFORM"

    def run(self, pixels, x, y, mode, invert) -> tuple[torch.Tensor, torch.Tensor]:
        pixels = comp.tensor2cv(pixels)
        while (len(mode) > 0):
            axis, mode = mode[0], mode[1:]
            px = [y, x][axis == 'X']
            pixels = comp.MIRROR(pixels, px, int(axis == 'X'), invert=invert)
        return (comp.cv2tensor(pixels), comp.cv2mask(pixels), )

class ExtendNode(JovimetrixBaseImageNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"required": {
                "axis": (["HORIZONTAL", "VERTICAL"], {"default": "HORIZONTAL"}),
            },
            "optional": {
                "flip": ("BOOLEAN", {"default": False}),
            },
        }
        return deep_merge_dict(IT_PIXEL2, d, IT_WH, IT_WHMODE)

    DESCRIPTION = "Contrast, Gamma and Exposure controls for images."
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/TRANSFORM"

    def run(self, pixelA: torch.tensor, pixelB: torch.tensor, axis: str, flip: str,
            width: int, height: int, mode: str) -> tuple[torch.Tensor, torch.Tensor]:

        pixelA = comp.SCALEFIT(comp.tensor2cv(pixelA), width, height, 'FIT')
        pixelB = comp.SCALEFIT(comp.tensor2cv(pixelB), width, height, 'FIT')

        pixelA = comp.EXTEND(pixelA, pixelB, axis, flip)
        if mode != "NONE":
            pixelA = comp.SCALEFIT(pixelA, width, height, mode)
        return (comp.cv2tensor(pixelA), comp.cv2mask(pixelA), )

class ProjectionNode(JovimetrixBaseImageNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"required": {
                "proj": (["SPHERICAL", "CYLINDRICAL"], {"default": "SPHERICAL"}),
            }}
        return deep_merge_dict(IT_IMAGE, d, IT_WH)

    DESCRIPTION = ""
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/**DO NOT USE**"

    def run(self, image: torch.tensor, proj: str, width: int, height: int) -> tuple[torch.Tensor, torch.Tensor]:
        image = comp.tensor2pil(image)

        source_width, source_height = image.size
        target_image = Image.new("RGB", (width, height))
        for y_target in range(height):
            for x_target in range(width):
                x_source = int((x_target / width) * source_width)

                if proj == "SPHERICAL":
                    x_source %= source_width
                y_source = int(y_target / height * source_height)
                px = image.getpixel((x_source, y_source))

                target_image.putpixel((x_target, y_target), px)
        return (comp.pil2tensor(target_image), comp.pil2mask(target_image),)

# =============================================================================
# === ADJUST LUMA/COLOR NODES ===
# =============================================================================

class HSVNode(JovimetrixBaseImageNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"required": {
                "hue": ("FLOAT",{"default": 0., "min": 0., "max": 1., "step": 0.01},),
                "saturation": ("FLOAT", {"default": 1.0, "min": 0., "max": 2., "step": 0.01}, ),
                "value": ("FLOAT", {"default": 1.0, "min": 0., "max": 100., "step": 0.01}, ),
                "contrast": ("FLOAT", {"default": 0., "min": 0., "max": 2., "step": 0.01}, ),
                "exposure": ("FLOAT", {"default": 1.0, "min": 0., "max": 2., "step": 0.01}, ),
                "gamma": ("FLOAT", {"default": 1.0, "min": 0., "max": 2., "step": 0.01}, ),
            }}
        return deep_merge_dict(IT_IMAGE, d, IT_INVERT)

    DESCRIPTION = "Adjust Hue, Saturation, Value, Gamma, Contrast and Exposure of an input"
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/ADJUST"

    def run(self, image: torch.tensor, hue: float, saturation: float, value: float, contrast: float,
            exposure: float, gamma: float, invert: float) -> tuple[torch.Tensor, torch.Tensor]:

        # loginfo(1, image.dtype, hue, saturation, value, contrast, exposure, gamma, invert)
        image = comp.tensor2cv(image)
        if hue != 0 or saturation != 1 or value != 1:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            if hue != 0:
                hue *= 255
                image[:, :, 0] = (image[:, :, 0] + hue) % 180

            if saturation != 1:
                image[:, :, 1] = np.clip(image[:, :, 1] * saturation, 0, 255)

            if value != 1:
                image[:, :, 2] = np.clip(image[:, :, 2] * value, 0, 255)
            image = cv2.cvtColor(image, cv2.COLOR_HSV2BGR)

        if contrast != 0:
            image = comp.CONTRAST(image, contrast)

        if exposure != 1:
            image = comp.EXPOSURE(image, exposure)

        if gamma != 1:
            image = comp.GAMMA(image, gamma)

        if invert != 0:
            image = comp.INVERT(image, invert)

        return (comp.cv2tensor(image), comp.cv2mask(image), )

# =============================================================================
# === ADJUST GEOMETRY NODES ===
# =============================================================================

class AdjustNode(JovimetrixBaseImageNode):
    OPS = {
        'BLUR': ImageFilter.GaussianBlur,
        'SHARPEN': ImageFilter.UnsharpMask,
    }

    OPS_PRE = {
        # PREDEFINED
        'EMBOSS': ImageFilter.EMBOSS,
        'FIND_EDGES': ImageFilter.FIND_EDGES,
    }

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        ops = list(AdjustNode.OPS.keys()) + list(AdjustNode.OPS_PRE.keys())
        d = {"required": {
                "func": (ops, {"default": "BLUR"}),
                "radius": ("INT", {"default": 1, "min": 0, "step": 1}),
            }}
        return deep_merge_dict(IT_PIXELS, d, IT_INVERT)

    DESCRIPTION = "Find Edges, Blur, Sharpen and Emobss an input"
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/ADJUST"

    def run(self, pixels: torch.tensor, func: str, radius: float, invert: float)  -> tuple[torch.Tensor, torch.Tensor]:
        pixels = comp.tensor2pil(pixels)

        if (op := AdjustNode.OPS.get(func, None)):
            pixels = pixels.filter(op(radius))
        elif (op := AdjustNode.OPS_PRE.get(func, None)):
            pixels = pixels.filter(op())

        if invert != 0:
            pixels = comp.pil2cv(pixels)
            pixels = comp.INVERT(pixels, invert)
            pixels = comp.cv2pil(pixels)
        return (comp.pil2tensor(pixels), comp.pil2tensor(pixels.convert("L")), )

class ThresholdNode(JovimetrixBaseImageNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"required": {
                "op": (comp.EnumThresholdName, {"default": comp.EnumThreshold.BINARY.name}),
                "adapt": (comp.EnumAdaptThresholdName, {"default": comp.EnumAdaptThreshold.ADAPT_NONE.name}),
                "threshold": ("FLOAT", {"default": 0.5, "min": 0., "max": 1., "step": 0.01},),
                "block": ("INT", {"default": 3, "min": 1, "max": 101, "step": 1},),
                "const": ("FLOAT", {"default": 0, "min": -1., "max": 1., "step": 0.01},),
            }}
        return deep_merge_dict(IT_PIXELS, d, IT_WHMODEI)

    DESCRIPTION = "Clip an input based on a mid point value"
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/ADJUST"

    def run(self, pixels: torch.tensor, op: str, adapt: str, threshold: float,
            block: int, const: float, width: int, height: int, mode: str, invert: float)  -> tuple[torch.Tensor, torch.Tensor]:

        pixels = comp.tensor2cv(pixels)
        # force block into odd
        if block % 2 == 0:
            block += 1

        op = comp.EnumThreshold[op].value
        adapt = comp.EnumAdaptThreshold[adapt].value
        pixels = comp.THRESHOLD(pixels, threshold, op, adapt, block, const)
        pixels = comp.SCALEFIT(pixels, width, height, mode)
        if invert:
            pixels = comp.INVERT(pixels)
        return (comp.cv2tensor(pixels), comp.cv2mask(pixels), )

# =============================================================================
# === COMPOSITION NODES ===
# =============================================================================

class BlendNodeBase(JovimetrixBaseImageNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"required": {
                "alpha": ("FLOAT", {"default": 1., "min": 0., "max": 1., "step": 0.01}),
            },
            "optional": {
                "func": (list(comp.OP_BLEND.keys()), {"default": "LERP"}),
        }}

        if cls == BlendMaskNode:
            e = {"optional": {
                    "mask": (WILDCARD, {"default": None})
                }}
            return deep_merge_dict(IT_PIXEL2, e, d, IT_WHMODEI)
        return deep_merge_dict(IT_PIXEL2, d, IT_WHMODEI)

    DESCRIPTION = "Applies selected operation to 2 inputs with optional mask using a linear blend (alpha)."
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/COMPOSE"

    def run(self, pixelA: torch.tensor, pixelB: torch.tensor, alpha: float, func: str, mask: torch.tensor,
            width: int, height: int, mode: str, invert) -> tuple[torch.Tensor, torch.Tensor]:

        pixelA = comp.tensor2cv(pixelA)
        pixelB = comp.tensor2cv(pixelB)
        mask = comp.tensor2cv(mask)
        pixelA = comp.BLEND(pixelA, pixelB, func, width, height, mask=mask, alpha=alpha)
        if invert:
            pixelA = comp.INVERT(pixelA, invert)
        pixelA = comp.SCALEFIT(pixelA, width, height, mode)
        return (comp.cv2tensor(pixelA), comp.cv2mask(pixelA),)

class BlendNode(BlendNodeBase):
    DESCRIPTION = "Applies selected operation to 2 inputs with optional mask using a linear blend (alpha)."

    def run(self, pixelA: torch.tensor, pixelB: torch.tensor, alpha: float, func: str,
            width: int, height: int, mode: str, invert) -> tuple[torch.Tensor, torch.Tensor]:

        mask = torch.ones((height, width))
        return super().run(pixelA, pixelB, alpha, func, mask, width, height, mode, invert)

class BlendMaskNode(BlendNodeBase):
    DESCRIPTION = "Applies selected operation to 2 inputs with using a linear blend (alpha)."

    def run(self, pixelA: torch.tensor, pixelB: torch.tensor, alpha: float, func: str, mask: torch.tensor,
            width: int, height: int, mode: str, invert) -> tuple[torch.Tensor, torch.Tensor]:

        return super().run(pixelA, pixelB, alpha, func, mask, width, height, mode, invert)

# =============================================================================
# === CAPTURE NODES ===
# =============================================================================

class StreamReaderNode(JovimetrixBaseImageNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        data = list(STREAMMANAGER.STREAM.keys())
        default = data[0] if len(data) > 0 else ""
        d = {"required": {
                "idx": (data, {"default": default}),
                "url": ("STRING", {"default": ""}),
                "fps": ("INT", {"min": 1, "max": 60, "step": 1, "default": 60}),
            },
            "optional": {
                "hold": ("BOOLEAN", {"default": False}),
            }}
        return deep_merge_dict(d, IT_WHMODEI, IT_ORIENT)

    DESCRIPTION = ""
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/STREAM"

    @classmethod
    def IS_CHANGED(cls, idx: int, url: str, fps: float, hold: bool, width: int, height: int, mode: str, invert: float, orient: str) -> float:
        """
        Check if StreamReader parameters have changed.

        Args:
            idx (int): Index of the StreamReader.
            url (str): URI for a streaming device.
            fps (float): Frames per second.
            hold (bool): Hold last frame flag.
            width (int): Width of the image.
            height (int): Height of the image.
            mode (str): Scale processing mode.
            invert (float): Amount to invert the output
            orient (str): Normal, FlipX, FlipY or FlipXY

        Returns:
            float: cached value.
        """

        url = url if url != "" else idx
        stream = STREAMMANAGER.capture(url)

        if stream.size[0] != width or stream.size[1] != height:
            stream.size = (width, height)

        if stream.fps != fps:
            stream.fps = fps

        return float("nan")

    def run(self, idx: int, url: str, fps: float, hold: bool, width: int, height: int, mode: str, invert: float, orient: str) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Return a current frame from the StreamReader if it is active and the FPS check passes.

        Args:
            idx (int): Index of the StreamReader.
            url (str): URI for a streaming device.
            fps (float): Frames per second.
            hold (bool): Hold last frame flag.
            width (int): Width of the image.
            height (int): Height of the image.
            mode (str): Scale processing mode.
            invert (float): Amount to invert the output
            orient (str): Normal, FlipX, FlipY or FlipXY

        Returns:
            (image (torch.tensor), mask (torch.tensor)): The image and its mask result.
        """

        _, image = STREAMMANAGER.frame(idx)
        if hold:
            STREAMMANAGER.pause(idx)
            return (comp.cv2tensor(image), comp.cv2mask(image), )

        image = comp.SCALEFIT(image, width, height, 'FIT')

        if orient in ["FLIPX", "FLIPXY"]:
            image = cv2.flip(image, 1)

        if orient in ["FLIPY", "FLIPXY"]:
            image = cv2.flip(image, 0)

        if invert != 0.:
            image = comp.INVERT(image, invert)

        return (comp.cv2tensor(image), comp.cv2mask(image), )

class StreamWriterNode(JovimetrixBaseNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"required": {
                "route": ("STRING", {"default": "/stream"}),
            },
            "optional": {
                "hold": ("BOOLEAN", {"default": False}),
            }}
        return deep_merge_dict(IT_IMAGE, d, IT_WHMODEI, IT_ORIENT)

    DESCRIPTION = ""
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/STREAM"

    @classmethod
    def IS_CHANGED(cls, hold: bool, width: int, height: int, mode: str, invert: float, orient: str) -> float:
        """
        Check if StreamReader parameters have changed.

        Args:
            hold (bool): Hold last frame flag.
            width (int): Width of the image.
            height (int): Height of the image.
            mode (str): Scale processing mode.
            invert (float): Amount to invert the output
            orient (str): Normal, FlipX, FlipY or FlipXY

        Returns:
            float: cached value.
        """

        return float("nan")

    def __init__(self, *arg, **kw) -> None:
        super(StreamWriterNode).__init__(self, *arg, **kw)
        self.__host = None
        self.__port = None

    def run(self, hold: bool, width: int, height: int, mode: str, invert: float, orient: str) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Return a current frame from the StreamReader if it is active and the FPS check passes.

        Args:
            hold (bool): Hold last frame flag.
            width (int): Width of the image.
            height (int): Height of the image.
            mode (str): Scale processing mode.
            invert (float): Amount to invert the output
            orient (str): Normal, FlipX, FlipY or FlipXY

        Returns:
            (image (torch.tensor), mask (torch.tensor)): The image and its mask result.
        """

        if STREAMHOST != self.__host or STREAMPORT != self.__port:
            # close old, if any

            # startup server
            pass

# =============================================================================
# === UTILITY NODES ===
# =============================================================================

class RouteNode(JovimetrixBaseImageNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {"required": {
            "o": (WILDCARD, {"default": None}),
        }}

    DESCRIPTION = "Wheels on the BUS pass the data through, around and around."
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/UTILITY"
    RETURN_TYPES = (WILDCARD,)
    RETURN_NAMES = ("🚌",)

    def run(self, o: object) -> [object, ]:
        return (o,)

class TickNode(JovimetrixBaseImageNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {},
            "optional": {
                "total": ("INT", {"min": 0, "default": 0, "step": 1}),
                # forces a MOD on total
                "loop": ("BOOLEAN", {"default": False}),
                # stick the current "count"
                "hold": ("BOOLEAN", {"default": False}),
                # manual total = 0
                "reset": ("BOOLEAN", {"default": False}),
            }}

    DESCRIPTION = "Periodic pulse exporting normalized, delta since last pulse and count."
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/UTILITY"
    RETURN_TYPES = ("INT", "FLOAT", "FLOAT", "FLOAT", )
    RETURN_NAMES = ("count 🧮", "0-1", "time", "🛆",)

    @classmethod
    def IS_CHANGED(cls, *arg, **kw) -> Any:
        return float("nan")

    def __init__(self, *arg, **kw) -> None:
        super().__init__(*arg, **kw)
        self.__count = 0
        # previous time, current time
        self.__time = time.time()
        self.__delta = 0

    def run(self, total: int, loop: bool, hold: bool, reset: bool) -> None:
        if reset:
            self.__count = 0

        count = self.__count
        if loop and total > 0:
            count %= total

        #sin = np.sin(self.__count)
        #cos = np.cos(self.__count)
        lin = (self.__count / total) if total != 0 else 1

        t = self.__time
        if not hold:
            self.__count += 1
            t = time.time()

        self.__delta = t - self.__time
        self.__time = t

        #sinT = np.sin(t)
        #cosT = np.cos(t)

        return (count, lin, t, self.__delta,)

class OptionsNode(JovimetrixBaseNode):
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "trig": (WILDCARD, {"default": None}),
            },
            "optional": {
                "info": ("BOOLEAN", {"default": False}),
                "warn": ("BOOLEAN", {"default": False}),
                "error": ("BOOLEAN", {"default": False}),
            }}

    DESCRIPTION = "Change Jovimetrix Global Options"
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/UTILITY"

    def __init__(self, *arg, **kw) -> None:
        super().__init__(*arg, **kw)
        self.__host = None
        self.__port = None

    def run(self, hold: bool, width: int, height: int, mode: str, invert: float, orient: str) -> tuple[torch.Tensor, torch.Tensor]:
        if STREAMHOST != self.__host or STREAMPORT != self.__port:
            # close old, if any

            # startup server
            pass

# =============================================================================
# === COMFYUI NODE MAP ===
# =============================================================================

NODE_CLASS_MAPPINGS = {
    # CREATE
    "🟪 Constant (jov)": ConstantNode,
    "✨ Shape Generator (jov)": ShapeNode,
    "🌊 Wave Generator (jov)": WaveGeneratorNode,
    "🔆 Pixel Shader (jov)": PixelShaderNode,
    "🔆 Pixel Shader Image (jov)": PixelShaderImageNode,

    # TRANSFORM
    "🌱 Transform (jov)": TransformNode,
    "🎇 Extend (jov)": ExtendNode,
    "🔰 Mirror (jov)": MirrorNode,
    "🔳 Tile (jov)": TileNode,

    # ADJUST
    "🌈 HSV (jov)": HSVNode,
    "🕸️ Adjust (jov)": AdjustNode,

    "📉 Threshold (jov)": ThresholdNode,

    # COMPOSE
    "⚗️ Blend (jov)": BlendNode,
    "⚗️ Blend Mask (jov)": BlendMaskNode,

    # CAPTURE
    "📺 StreamReader (jov)": StreamReaderNode,
    "🎞️ StreamWriter (jov)": StreamWriterNode,

    # UTILITY
    "🚌 Route (jov)": RouteNode,
    "🕛 Tick (jov)": TickNode,
    "⚙️ Options (jov)": OptionsNode,


    # WIP OR BROKEN -- DO NOT USE IN FLOWS

    "🍩 GLSL (jov)": GLSLNode,
    "🗺️ Projection (jov)": ProjectionNode,
}

# 🔗 ⚓ 🎹 📀 🍿 🎪 🐘

NODE_DISPLAY_NAME_MAPPINGS = {k: k for k in NODE_CLASS_MAPPINGS}
