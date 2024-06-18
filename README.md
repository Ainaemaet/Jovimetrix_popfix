<h2><p align="center">THIS ENTIRE PROJECT IS DONATIONWARE.<br>PLEASE FEEL FREE TO CONTRIBUTE IN ANYWAY YOU THINK YOU CAN</p></h2>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github.com/Amorano/Jovimetrix-examples/blob/master/res/logo-jovimetrix.png">
  <source media="(prefers-color-scheme: light)" srcset="https://github.com/Amorano/Jovimetrix-examples/blob/master/res/logo-jovimetrix-light.png">
  <img alt="ComfyUI Nodes for procedural masking, live composition and video manipulation">
</picture>

<h3><p align="center">
<a href="https://github.com/comfyanonymous/ComfyUI">COMFYUI</a> Nodes for procedural masking, live composition and video manipulation
</p></h3>

<!---------------------------------------------------------------------------->

# WHY BUILD THESE NODES?

There are many ways to do composition and it is apparent that is a large portion of what Computer Vision - aka contemporaneous "A.I" - is invented to resolve.

While diffusers and latent hallucinations can make many amazing things at the moment, there is still a need to resolve final "frames" in something else, like one of the many free tools:
* [Krita](https://krita.org/en/) (2D)
* [Calvary](https://cavalry.scenegroup.co/) (motion graphics)
* [Davinci Resolve](https://www.blackmagicdesign.com/products/davinciresolve) (movie editing)

The main goal of Jovimetrix is to supplement those external workflows before the need to use them.

## TARGETS

* animation / motion graphics
* traditional image blending
* support masks as an image channel
* improved UX
** custom node colorization
** node favorites

# COMMUNITY

Everything here is made because I wanted to make it.
Everything you are looking for here that you cant find doesn't exist because I didn't make it.
If you feel like helping with text or code contributions, please pull and send me any PRs.

## VISUAL AIDS AND EXAMPLES

[![YouTube](./res/YouTube.svg)](https://www.youtube.com/channel/UCseaPIn-a2ji3LzVmnEF0Xw)

## WORKFLOW EXAMPLES

TBD

## CONTRIBUTIONS

Feel free to contribute to this project by reporting issues or suggesting improvements. Open an issue or submit a pull request on the GitHub repository.

## DONATIONS

[![If you feel like donating money resource instead, you can always use my ko-fi ❤️](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/alexandermorano)

## DISCORD
There are a few places you can chat about Jovimetrix nodes.

Directly on the `#jovimetrix` channel at the Banodoco discord:
[![](https://dcbadge.vercel.app/api/server/fbpScsxF4f?style=flat-square)](https://discord.gg/fbpScsxF4f)

On Purz discord (Creative Exploration):
[![](https://dcbadge.vercel.app/api/server/AxjQCRCnxn?style=flat-square)](https://discord.gg/AxjQCRCnxn)

# INSTALLATION

## COMFYUI MANAGER

If you have [ComfyUI Manager](https://github.com/ltdrdata/ComfyUI-Manager) installed, simply search for Jovimetrix and install from the manager's database.

## MANUAL INSTALL
Clone the repository into your ComfyUI custom_nodes directory. You can clone the repository with the command:
```
git clone https://github.com/Amorano/Jovimetrix.git
```
You can then install the requirements by using the command:
```
.\python_embed\python.exe -s -m pip install -r requirements.txt
```
If you are using a <code>virtual environment</code> (<code><i>venv</i></code>), make sure it is activated before installation. Then install the requirements with the command:
```
pip install -r requirements.txt
```

## ENVIRONMENT VARIABLES

### LOGGER

The logger can be controlled via the JOV_LOG_LEVEL variable. It can be set to one of the following, by name or value:

* TRACE (5)
* DEBUG (10)
* INFO (20)
* SUCCESS (25)
* WARNING (30)
* ERROR (40)
* CRITICAL (50)

The default is WARNING (30); i.e.:

`SET JOV_LOG_LEVEL=WARNING`

### IGNORE NODES

Because there are a number of nodes that have overlapping functionality with other node packages, I have provided a mechanism to ignore loading of specific nodes.

If you create a file called `ignore.txt` inside the Jovimetrix root folder \(`.../ComfyUI/custom_nodes/Jovimetrix`\), it will skip loading any nodes included.

#### USAGE

Each entry should be on a separate line using the full node class name (the default name of the node). For example, in ignore.txt:

`CONSTANT (JOV) 🟪`

Will ignore the Constant node for use in ComfyUI.

This will *NOT* prevent the module from loading the imports, but this can help reduce your visual space while working within ComfyUI if you do not require looking at an additional 60+ nodes.


### SYSTEM DEVICE SCAN

Allows the system to auto-scan for any devices, so that it can populate the device list in the Stream Reader Node.

The [STREAM READER📺](https://github.com/Amorano/Jovimetrix/wiki/DEVICE#-stream-reader) is able to load media from local media, web media dna also system devices such as (virtual) web cameras and monitors. By default, the scan for web cameras is off.

If you wish to engage the auto-scan on ComfyUI start-up, set the JOV_SCAN_DEVICES variable to 1 or True.

`SET JOV_SCAN_DEVICES=1`

### HELP SYSTEM

The main help system is made possible by [Mel Massadian](https://github.com/melMass). It is located on the top right of each node (?). This will present a window which is loaded from the [main help repository for Jovimetrix](https://github.com/Amorano/Jovimetrix-examples/)

You can build all the help locally by loading Comfy and surfing to the local URL:

`http://127.0.0.1:8188/jovimetrix/doc`

This will build all the help stub files (.md) inside the main Jovimetrix folder under a folder named `_md`

If you wish to re-direct those outputs, you can set the ENV varible `JOV_SIDECAR`.

e.g.
`SET JOV_SIDECAR=C:/dev/jvx/help`

### GIFSKI SUPPORT

If you have [GIFSKI](https://gif.ski/) installed you can enable the option for the Export Node to use GIFSKI when outputting frames.

You will need to add an environment var so it knows you have it installed and where:

`SET JOV_GIFSKI=[path to gifski]`

Once set the GIFSKI option should appear in the Export Node drop down list of output target formats.

### PYAUDIO

By default, pyaudio is installed for all platforms; however, it may be nessicary to run a specific platform package manager to obtain all the correct platform dependencies. [You can refer to the non-complicated specific platform instructions for help.](https://people.csail.mit.edu/hubert/pyaudio).

In short:
* For MacOS you need the extra brew package of portaudio. (brew install portaudio)
* For Linux you need the extra apt package of python3-pyaudio. (sudo apt-get install python3-pyaudio)

### SPOUT (WINDOWS ONLY)

If you are on Linux or Mac, `Spout` will not be installed from the requirements.txt.

By default, [Spout](https://leadedge.github.io/), a system for GPU accelerated sharing
of graphics between applications, is on for all platforms.

If you are on Mac or Linux, this will only amount to a message at startup about Spout not being used. When Spout is not found, the SpoutWriter node will not showup. In addition, the StreamReader node will not have Spout as an option from which to read stream data.

If you want to fully turn off the initial startup attempt to import Spout, you can use the environment variable:

`SET JOV_SPOUT=0`

## FFMEPG

The audio nodes require FFMPEG. You can find the official [FFMPEG](https://ffmpeg.org "official FFMPEG binaries") here. Follow it's installation instructions for your specific operating system.

<!---------------------------------------------------------------------------->

# [NODE REFERENCE](https://github.com/Amorano/Jovimetrix/wiki)

[CREATE](https://github.com/Amorano/Jovimetrix/wiki/CREATE#create) | &nbsp;
---|---
[CONSTANT 🟪](https://github.com/Amorano/Jovimetrix/wiki/CREATE#-constant)|Create a single RGBA block of color. Useful for masks, overlays and general filtering.
[SHAPE GEN ✨](https://github.com/Amorano/Jovimetrix/wiki/CREATE#-shape-generator)|Generate polyhedra for masking or texture work.
[TEXT GEN 📝](https://github.com/Amorano/Jovimetrix/wiki/CREATE#-text-generator)|Uses any system font with auto-fit or manual placement.
[STEREOGRAM 📻](https://github.com/Amorano/Jovimetrix/wiki/CREATE#-stereogram)|Make a magic eye stereograms.
[STEREOSCOPIC 🕶️](https://github.com/Amorano/Jovimetrix/wiki/CREATE#-stereoscopic)|Simulate depth perception in images by generating stereoscopic views.
[GLSL 🍩](https://github.com/Amorano/Jovimetrix/wiki/CREATE#-glsl)|GLSL Shader support
[GRAPH WAVE▶ ılıılı](https://github.com/Amorano/Jovimetrix/wiki/CREATE#-graph-wave)|Import and display audio linear waveform data.
<img width=225/>|<img width=800/>

[COMPOSE](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE) | &nbsp;
---|---
[ADJUST 🕸️](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE#-adjust)|Blur, Sharpen, Emboss, Levels, HSV, Edge detection.
[BLEND ⚗️](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE#-blend)|Applies selected operation to 2 inputs with optional mask using a linear blend (alpha)
[COLOR BLIND 👁‍🗨](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE#-color-blind)|Simulate color blindness effects on images.
[COLOR MATCH 💞](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE#-color-match)|Project the colors of one image  onto another or use a pre-defined color target.
[COLOR THEORY 🛞](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE#-color-theory)|Generate Complimentary, Triadic and Tetradic color sets
[CROP ✂️](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE#-crop)|Clip away sections of an image and backfill with optional color matte
[FILTER MASK 🤿](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE#-filter-mask)|Create masks based on specific color ranges within an image.
[FLATTEN ⬇️](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE#-flatten)|Combine multiple input images into a single image by summing their pixel values
[PIXEL MERGE 🫂](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE#-pixel-merge)|Combine 3 or 4 inputs into a single image
[PIXEL SPLIT 💔](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE#-pixel-split)|Splits images into constituent R, G and B and A channels
[PIXEL SWAP 🔃](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE#-pixel-swap)|Swap pixel values between two input images based on specified channel swizzle operations
[STACK ➕](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE#-stack)|Union multiple latents horizontal, vertical or in a grid
[THRESHOLD 📉](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE#-threshold)|Clip an input based on a mid point value.
[TRANSFORM 🏝️](https://github.com/Amorano/Jovimetrix/wiki/COMPOSE#-transform)|Translate, Rotate, Scale, Tile, Mirror, Re-project and invert an input
<img width=225/>|<img width=800/>

[CALCULATE](https://github.com/Amorano/Jovimetrix/wiki/CALCULATE) | &nbsp;
---|---
[COMPARISON 🕵🏽](https://github.com/Amorano/Jovimetrix/wiki/CALCULATE#-comparison)|Compare two inputs: A=B, A!=B, A>B, A>=B, A<B, A<=B
[DELAY ✋🏽](https://github.com/Amorano/Jovimetrix/wiki/CALCULATE#-delay)|Delay traffic. Electrons on the data bus go round.
[LERP 🔰](https://github.com/Amorano/Jovimetrix/wiki/CALCULATE#-lerp)|Interpolate between two values with or without a smoothing
[OP UNARY 🎲](https://github.com/Amorano/Jovimetrix/wiki/CALCULATE#-calc-op-unary)|Perform a Unary Operation on an input.
[OP BINARY 🌟](https://github.com/Amorano/Jovimetrix/wiki/CALCULATE#-calc-op-binary)|Perform a Binary Operation on two inputs.
[TICK ⏱](https://github.com/Amorano/Jovimetrix/wiki/CALCULATE#-tick)|Periodic pulse exporting normalized, delta since last pulse and count.
[VALUE #️⃣](https://github.com/Amorano/Jovimetrix/wiki/CALCULATE-value)|Create a value for most types; also universal constants.
[WAVE GEN 🌊](https://github.com/Amorano/Jovimetrix/wiki/CALCULATE#-wave_generator)|Periodic and Non-Periodic Sinosodials.
<img width=225/>|<img width=800/>

[DEVICE](https://github.com/Amorano/Jovimetrix/wiki/DEVICE) | &nbsp;
---|---
[MIDI FILTER ✳️](https://github.com/Amorano/Jovimetrix/wiki/DEVICE#%EF%B8%8F-midi-filter)|Filter MIDI messages by channel, message type or value.
[MIDI FILTER EZ ❇️](https://github.com/Amorano/Jovimetrix/wiki/DEVICE#%EF%B8%8F-midi-filter-ez)|Filter MIDI messages by channel, message type or value.
[MIDI MESSAGE 🎛️](https://github.com/Amorano/Jovimetrix/wiki/DEVICE#%EF%B8%8F-midi-message)|Expands a MIDI message into its values.
[MIDI READER 🎹](https://github.com/Amorano/Jovimetrix/wiki/DEVICE#-midi-reader)|Capture MIDI devices and pass the data into Comfy.
[STREAM READER 📺](https://github.com/Amorano/Jovimetrix/wiki/DEVICE#-stream-reader)|Connect system media devices and remote streams into ComfyUI workflows.
[STREAM WRITER 🎞️](https://github.com/Amorano/Jovimetrix/wiki/DEVICE#%EF%B8%8F-stream-writer)|Broadcast ComfyUI Node outputs to custom webserver endpoint.
<img width=225/>|<img width=800/>

[UTILITY](https://github.com/Amorano/Jovimetrix/wiki/UTILITY) | &nbsp;
---|---
[AKASHIC 📓](https://github.com/Amorano/Jovimetrix/wiki/UTILITY#-akashic)|Display the top level attributes of an output
[EXPORT 📽](https://github.com/Amorano/Jovimetrix/wiki/UTILITY#-export)|Take your frames out static or animated (GIF)
[GRAPH 📈](https://github.com/Amorano/Jovimetrix/wiki/UTILITY#-value-graph)|Graphs historical execution run values
[QUEUE 🗃](https://github.com/Amorano/Jovimetrix/wiki/UTILITY#-queue)|Cycle lists of images files or strings for node inputs.
[ROUTE 🚌](https://github.com/Amorano/Jovimetrix/wiki/UTILITY#-route)|Pass all data because the default is broken on connection
[SAVE OUTPUT 💾](https://github.com/Amorano/Jovimetrix/wiki/UTILITY#-save-output)|Select an item from a user explicit list of inputs.
<img width=225/>|<img width=800/>

<!---------------------------------------------------------------------------->

# ACKNOWLEDGEMENTS

Everyone mentioned here has been tireless in helping me, at some point, construct all the material in Jovimetrix.

&nbsp; | &nbsp;
---|---
[Stable Diffusion](https://stability.ai/stable-diffusion/)|without this, we would all still only be using pixel pushing tools
[ComfyUI](https://github.com/comfyanonymous/ComfyUI)|Thank You! for existing
<img width=225/>|<img width=auto/>

## COMFY DEVELOPERS & NODE MAKERS & COMMUNITY BUILDERS

&nbsp; | &nbsp; | &nbsp;
---|---|---
[comfy](https://github.com/comfyanonymous)|[Chris Goringe](https://github.com/chrisgoringe)|[Purz](https://github.com/purzbeats)
[pythongosssss](https://github.com/pythongosssss)|[melmass](https://github.com/melMass)|[Fizzledorf](https://github.com/Fizzledorf)
[Dr. Lt. Data](https://github.com/ltdrdata)|[Trung0246](https://github.com/Trung0246)|[Fannovel16](https://github.com/Fannovel16)
[Kijai](https://github.com/Kijai)|[WASasquatch](https://github.com/WASasquatch)|[MatisseTec](https://github.com/MatissesProjects)
[rgthree](https://github.com/rgthree)|[Suzue1](https://github.com/Suzie1)
<img width=250/>|<img width=250/>|<img width=250/>

<!---------------------------------------------------------------------------->

# LICENSE

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.