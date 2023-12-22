"""
Jovimetrix - http://www.github.com/amorano/jovimetrix
Transformation
"""

from typing import Optional

import numpy as np
import torch

from Jovimetrix import parse_tuple, parse_number, zip_longest_fill, deep_merge_dict, \
    tensor2cv, cv2mask, cv2tensor, \
    EnumTupleType, JOVImageInOutBaseNode, Logger, Lexicon, \
    IT_PIXELS, IT_TRS, IT_WH, IT_REQUIRED, IT_EDGE, \
    IT_WHMODE, MIN_IMAGE_SIZE, IT_TILE, IT_XY, IT_INVERT

from Jovimetrix.sup import comp
from Jovimetrix.sup.comp import geo_transform, geo_edge_wrap, geo_scalefit, geo_mirror, \
    remap_fisheye, remap_sphere, light_invert, \
    EnumScaleMode, EnumProjection, EnumMirrorMode, EnumInterpolation, IT_SAMPLE

# =============================================================================

class TransformNode(JOVImageInOutBaseNode):
    NAME = "TRANSFORM (JOV) 🏝️"
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/TRANSFORM"
    DESCRIPTION = "Translate, Rotate, Scale, Tile and Invert an input. CROP or WRAP the edges."

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return deep_merge_dict(IT_REQUIRED, IT_PIXELS, IT_TRS, IT_EDGE, IT_WH, IT_WHMODE, IT_SAMPLE)

    def run(self, **kw) -> tuple[torch.Tensor, torch.Tensor]:
        pixels = kw.get(Lexicon.PIXEL, [None])
        offset = parse_tuple(Lexicon.OFFSET, kw, default=(0, 0,), clip_min=-1, clip_max=1)
        angle = kw.get(Lexicon.ANGLE, [None])
        size = parse_tuple(Lexicon.SIZE, kw, default=(1, 1,), clip_min=0, clip_max=1)
        wihi = parse_tuple(Lexicon.WH, kw, default=(MIN_IMAGE_SIZE, MIN_IMAGE_SIZE,), clip_min=1)
        edge = kw.get(Lexicon.EDGE, [None])
        mode = kw.get(Lexicon.MODE, [None])
        sample = kw.get(Lexicon.SAMPLE, [None])
        masks = []
        images = []
        for data in zip_longest_fill(pixels, *offset, angle, *size, edge, *wihi, mode, sample):
            img, oX, oY, a, sX, sY, e, w, h, m, rs = data
            if img is not None:
                img = tensor2cv(img)
                rs = EnumInterpolation[rs] if rs is not None else EnumInterpolation.LANCZOS4
                img = geo_transform(img, oX, oY, a, sX, sY, e, w, h, m, rs)
            else:
                img = np.zeros((h, w, 3), dtype=np.uint8)
            images.append(cv2tensor(img))
            masks.append(cv2mask(img))

        return (
            torch.stack(images),
            torch.stack(masks)
        )

class TileNode(JOVImageInOutBaseNode):
    NAME = "TILE (JOV) 🀘"
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/TRANSFORM"
    DESCRIPTION = "Tile an Image with optional crop to original image size."
    SORT = 5

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return deep_merge_dict(IT_REQUIRED, IT_PIXELS, IT_TILE, IT_WH, IT_WHMODE, IT_SAMPLE)

    def run(self, **kw) -> tuple[list[torch.Tensor], list[torch.Tensor]]:

        pixels = kw.get(Lexicon.PIXEL, [None])
        tile = parse_tuple(Lexicon.XY, kw, default=(2, 2,), clip_min=1)
        wihi = parse_tuple(Lexicon.WH, kw, default=(MIN_IMAGE_SIZE, MIN_IMAGE_SIZE,), clip_min=1)
        mode = kw.get(Lexicon.MODE, [None])
        sample = kw.get(Lexicon.SAMPLE, [None])
        masks = []
        images = []
        for data in zip_longest_fill(pixels, *tile, *wihi, mode, sample):
            img, x, y, w, h, m, rs = data
            img = tensor2cv(img) if img is not None else np.zeros((h, w, 3), dtype=np.uint8)
            img = geo_edge_wrap(img, x, y)
            rs = EnumInterpolation[rs] if rs is not None else EnumInterpolation.LANCZOS4
            img = geo_scalefit(img, w, h, m, rs)
            images.append(cv2tensor(img))
            masks.append(cv2mask(img))

        return (
            torch.stack(images),
            torch.stack(masks)
        )

class MirrorNode(JOVImageInOutBaseNode):
    NAME = "MIRROR (JOV) 🔰"
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/TRANSFORM"
    DESCRIPTION = "Flip an input across the X axis, the Y Axis or both, with independent centers."
    SORT = 25

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"optional": {
                Lexicon.MIRROR: (EnumMirrorMode._member_names_, {"default": EnumMirrorMode.X.name}),
            }}
        return deep_merge_dict(IT_PIXELS, d, IT_XY, IT_INVERT)

    def run(self, **kw) -> tuple[list[torch.Tensor], list[torch.Tensor]]:
        pixels = kw.get(Lexicon.PIXEL, [None])
        offset = parse_tuple(Lexicon.XY, kw, default=(0, 0,), clip_min=-1, clip_max=1)
        i = parse_number(Lexicon.INVERT, kw, EnumTupleType.FLOAT, default=[1], clip_min=0, clip_max=1)
        mode = kw.get(Lexicon.MODE, [None])
        masks = []
        images = []
        for data in zip_longest_fill(pixels, *offset, mode, i):
            img, x, y, m, i = data
            img = tensor2cv(img) if img is not None else np.zeros((0,0,3), dtype=np.uint8)
            if 'X' in m:
                img = geo_mirror(img, x or 0, 1, invert=i or 0)
            if 'Y' in m:
                img = geo_mirror(img, y or 0, 0, invert=i or 0)

            images.append(cv2tensor(img))
            masks.append(cv2mask(img))

        return (
            torch.stack(images),
            torch.stack(masks)
        )

class ProjectionNode(JOVImageInOutBaseNode):
    NAME = "PROJECTION (JOV) 🗺️"
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/TRANSFORM"
    DESCRIPTION = ""
    SORT = 55

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = {"optional": {
                Lexicon.PROJECTION: (EnumProjection._member_names_, {"default": EnumProjection.SPHERICAL.name}),
                Lexicon.STRENGTH: ("FLOAT", {"default": 1, "min": 0, "step": 0.01}),
            }}
        return deep_merge_dict(IT_PIXELS, d, IT_WHMODE, IT_SAMPLE, IT_INVERT)

    def run(self, **kw) -> tuple[torch.Tensor, torch.Tensor]:
        pixels = kw.get(Lexicon.PIXEL, [None])
        wihi = parse_tuple(Lexicon.WH, kw, default=(MIN_IMAGE_SIZE, MIN_IMAGE_SIZE,), clip_min=1)
        i = parse_number(Lexicon.INVERT, kw, EnumTupleType.FLOAT, [1], clip_min=0, clip_max=1)
        proj = kw.get(Lexicon.PROJECTION, [None])
        strength = kw.get(Lexicon.STRENGTH, [None])
        mode = kw.get(Lexicon.MODE, [None])
        sample = kw.get(Lexicon.SAMPLE, [None])
        masks = []
        images = []
        for data in zip_longest_fill(pixels, proj, strength, *wihi, mode, i, sample):
            img, pr, st, w, h, m, i, rs = data
            st = st if st is not None else 1
            pr = pr if pr is not None else EnumProjection.SPHERICAL
            m = m if m is not None else EnumScaleMode.NONE
            img = tensor2cv(img) if img is not None else np.zeros((h, w, 3), dtype=np.uint8)
            match pr:
                case EnumProjection.SPHERICAL:
                    img = remap_sphere(img, st)
                case EnumProjection.FISHEYE:
                    img = remap_fisheye(img, st)

            rs = EnumInterpolation[rs] if rs is not None else EnumInterpolation.LANCZOS4
            img = geo_scalefit(img, w, h, m, rs)
            if (i if i is not None else 0) != 0:
                img = light_invert(img, i)

            images.append(cv2tensor(img))
            masks.append(cv2mask(img))

        return (
            torch.stack(images),
            torch.stack(masks)
        )
