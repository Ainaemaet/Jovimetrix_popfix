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
@description: Remapping images to new perspectives.
"""

from PIL import Image
from .. import IT_WH, IT_IMAGE, deep_merge_dict
from ..util import JovimetrixBaseNode, pil2tensor, tensor2pil

__all__ = ["MappingNode"]

# =============================================================================
class MappingNode(JovimetrixBaseNode):
    @classmethod
    def INPUT_TYPES(s):
        d = {"required": {
                "proj": (["SPHERICAL", "CYLINDRICAL"], {"default": "SPHERICAL"}),
            }}
        return deep_merge_dict(IT_IMAGE, d, IT_WH)

    DESCRIPTION = ""
    CATEGORY = "JOVIMETRIX 🔺🟩🔵/Image"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image", )

    def run(self, image, proj, width, height):
        image = tensor2pil(image)

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
        return (pil2tensor(target_image),)

NODE_CLASS_MAPPINGS = {
    "🗺️ Remap Image (jov)": MappingNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {k: k for k in NODE_CLASS_MAPPINGS}
