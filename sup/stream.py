"""
Jovimetrix - http://www.github.com/amorano/jovimetrix
Media Stream Support
"""

import os
import json
import time
import threading
from typing import Any, Optional
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import numpy as np

from Jovimetrix import Logger, Singleton
from Jovimetrix.sup.comp import geo_scalefit, image_grid, EnumScaleMode, EnumInterpolation

# =============================================================================

class StreamMissingException(Exception): pass

# =============================================================================
# === GLOBAL CONFIG ===
# =============================================================================

STREAMHOST = os.getenv("JOV_STREAM_HOST", '')
STREAMPORT = 7227
try: STREAMPORT = int(os.getenv("JOV_STREAM_PORT", STREAMPORT))
except: pass

# =============================================================================
# === MEDIA ===
# =============================================================================

class MediaStreamBase:

    TIMEOUT = 1.

    def __init__(self,
                 url:int|str,
                 callback_frame:object,
                 width:int=320,
                 height:int=240,
                 fps:float=30,
                 mode:Optional[EnumScaleMode]=EnumScaleMode.FIT,
                 sample:Optional[EnumInterpolation]=EnumInterpolation.LANCZOS4,
                 ) -> None:

        self.__quit = False
        self.__paused = False
        self.__captured = False
        self.__ret = False
        self.__fps = fps
        self.__mode = mode
        self.__sample = sample
        self.__url = url
        try: self.__url = int(url)
        except: pass

        self.width = width
        self.height = height
        self.__timeout = None
        self.__callback_frame = callback_frame
        self.__frame = np.zeros((self.__height, self.__width, 3), dtype=np.uint8)
        self.__thread = threading.Thread(target=self.__run, daemon=True)
        self.__thread.start()

    def run(self) -> tuple[bool, Any]:
        return True, self.__frame

    def capture(self) -> None:
        time.sleep(0.1)
        return True

    def __run(self) -> None:
        while not self.__quit:

            delta = 1. / self.__fps
            waste = time.perf_counter() + delta

            if not self.__paused:
                if not self.__captured:
                    pause = self.__paused
                    self.__paused = True

                    if not self.capture():
                        Logger.err("MediaStream", f"CAPTURE FAIL [{self.__url}]")
                        self.__quit = True
                        break

                    self.__paused = pause
                    self.__captured = True
                    Logger.info("MediaStream", f"CAPTURED [{self.__url}]")

                # call the run capture frame command on subclasses
                newframe = None
                if self.__callback_frame:
                    # Logger.spam('callback')
                    self.__ret, newframe = self.__callback_frame()

                if newframe is not None:
                    newframe = geo_scalefit(newframe, self.__width,
                                     self.__height, self.__mode, self.__sample)

                    self.__frame = newframe
                    self.__timeout = None

                if self.__timeout is None and (not self.__ret or newframe is None):
                    self.__timeout = time.perf_counter() + self.TIMEOUT

            if self.__timeout is not None and time.perf_counter() > self.__timeout:
                self.__timeout = None
                self.__quit = True
                Logger.warn("MediaStream", f"TIMEOUT [{self.__url}]")

            waste = max(waste - time.perf_counter(), delta)
            # Logger.debug(waste)
            time.sleep(waste)

        Logger.info("MediaStream", f"STOPPED [{self.__url}]")
        self.end()

    def __del__(self) -> None:
        self.end()

    def end(self) -> None:
        self.release()
        self.__quit = True
        Logger.warn("MediaStream", f"END [{self.__url}]")

    def release(self) -> None:
        self.__captured = False
        Logger.warn("MediaStream", f"RELEASED [{self.__url}]")

    def play(self) -> None:
        self.__paused = False

    def pause(self) -> None:
        self.__paused = True
        Logger.warn("MediaStream", f"PAUSED [{self.__url}]")

    def sizer(self, width:int, height:int) -> None:
        self.width = width
        self.height = height

    @property
    def captured(self) -> bool:
        return self.__captured

    @property
    def url(self) -> str:
        return self.__url

    @property
    def frame(self) -> tuple[bool, Any]:
        return self.__ret, self.__frame

    @property
    def width(self) -> int:
        return self.__width

    @width.setter
    def width(self, val) -> None:
        self.__width = max(1, val)

    @property
    def height(self) -> int:
        return self.__height

    @height.setter
    def height(self, val) -> None:
        self.__height = max(1, val)

    @property
    def scalemode(self) -> EnumScaleMode:
        return self.__scalemode

    @scalemode.setter
    def scalemode(self, val: EnumScaleMode) -> None:
        self.__scalemode = val

    @property
    def sample(self) -> EnumInterpolation:
        return self.__sample

    @sample.setter
    def sample(self, val: EnumInterpolation) -> None:
        self.__sample = val

    @property
    def fps(self) -> float:
        return self.__fps

    @fps.setter
    def fps(self, val: float) -> None:
        self.__fps = max(1, val)
        Logger.debug("MediaStream", f"FPS ({val}) [{self.url}]")

class MediaStreamDevice(MediaStreamBase):
    TIMEOUT = 5.
    def __init__(self, url:int|str, width:int=320, height:int=240, fps:float=30,
                 mode:Optional[EnumScaleMode]=EnumScaleMode.NONE,
                 sample:Optional[EnumInterpolation]=EnumInterpolation.LANCZOS4,
                 backend:int=None) -> None:

        self.__source = None
        self.__backend = [backend] if backend else [cv2.CAP_ANY]
        self.__zoom = 0
        self.__focus = 0
        self.__exposure = 1
        super().__init__(url, self.__callback, width, height, fps, mode, sample)

    def __callback(self) -> tuple[bool, Any]:
        if self.__source is None:
            return False, None

        ret = False
        newframe = None
        try:
            ret, newframe = self.__source.read()
        except:
            pass

        if not ret:
            try:
                # for cameras will just ignore; reached the end of the source
                count = self.__source.get(cv2.CAP_PROP_FRAME_COUNT)
                pos = self.__source.get(cv2.CAP_PROP_POS_FRAMES)
                if pos >= count:
                    self.__source.set(cv2.CAP_PROP_POS_FRAMES, 0)
            except:
                pass

        return ret, newframe

    def capture(self) -> bool:
        if self.captured:
            return True

        timeout = time.perf_counter() + self.TIMEOUT
        while self.__source is None and time.perf_counter() < timeout:
            self.__source = None
            for x in self.__backend:
                self.__source = cv2.VideoCapture(self.url, x)
                if self.captured:
                    Logger.debug(f"CAPTURED {self.__source.getBackendName()}")
                    time.sleep(0.4)
                    return True
        return False

    def end(self) -> None:
        super().end()
        try:
            if self.__thread:
                self.__thread.join()
                del self.__thread
        except AttributeError as _:
            pass

    def sizer(self, width:int, height:int) -> None:
        self.__source.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.__source.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        super().sizer(width, height)

    @property
    def captured(self) -> bool:
        if self.__source is None:
            return False
        return self.__source.isOpened()

    def release(self) -> None:
        if self.__source:
            self.__source.release()
        super().release()

    @property
    def zoom(self) -> float:
        return self.__zoom

    @zoom.setter
    def zoom(self, val: float) -> None:
        self.__zoom = np.clip(val, 0, 1)
        val = 100 + 300 * self.__zoom
        self.__source.set(cv2.CAP_PROP_ZOOM, val)
        Logger.debug("MediaStream", f"ZOOM ({self.__zoom})")

    @property
    def exposure(self) -> float:
        return self.__exposure

    @exposure.setter
    def exposure(self, val: float) -> None:
        # -10 to -1 range
        self.__exposure = np.clip(val, 0, 1)
        val = -10 + 9 * self.__exposure
        self.__source.set(cv2.CAP_PROP_EXPOSURE, val)

    @property
    def focus(self) -> float:
        return self.__focus

    @focus.setter
    def focus(self, val: float) -> None:
        self.__focus = np.clip(val, 0, 1)
        val = 255 * self.__focus
        self.__source.set(cv2.CAP_PROP_FOCUS, val)

class MediaStreamComfyUI(MediaStreamBase):
    """A stream coming from a comfyui node."""

    def run(self, image: cv2.Mat) -> tuple[bool, cv2.Mat]:
        return True, image

    def capture(self) -> bool:
        return True

class StreamManager(metaclass=Singleton):
    STREAM = {}
    @classmethod
    def devicescan(cls) -> None:
        """Indexes all devices that responded and if they are read-only."""

        def callback(stream, *arg) -> None:
            i = arg[0]
            StreamManager.STREAM[i] = stream

        for stream in StreamManager.STREAM.values():
            if stream:
                del stream
        StreamManager.STREAM = {}

        start = time.perf_counter()

        for i in range(5):
            stream = MediaStreamDevice(i, callback=(callback, i,) )

        Logger.info(f"SCAN ({time.perf_counter()-start:.4})")

    def __init__(self) -> None:
        #StreamManager.devicescan()
        Logger.info(f"STREAM {self.streams}")

    def __del__(self) -> None:
        if StreamManager:
            for c in StreamManager.STREAM.values():
                del c

    @property
    def streams(self) -> list[str|int]:
        return list(StreamManager.STREAM.keys())

    @property
    def active(self) -> list[MediaStreamDevice]:
        return [stream for stream in StreamManager.STREAM.values() if stream.captured]

    def frame(self, url: str) -> tuple[bool, Any]:
        if (stream := StreamManager.STREAM.get(url, None)) is None:
            # attempt to capture first time...
            stream = self.capture(url)

        #if not stream.captured:
        #    stream.capture()

        return stream.frame

    def capture(self, url: str, width:int=320, height:int=240, fps:float=30,
                backend:int=None, static:bool=False, endpoint:str=None) -> MediaStreamBase:

        if (stream := StreamManager.STREAM.get(url, None)) is None:
            if static:
                stream = StreamManager.STREAM[url] = MediaStreamComfyUI(url, width, height, fps)
                # Logger.debug(url, "MediaStreamComfyUI")
            else:
                stream = StreamManager.STREAM[url] = MediaStreamDevice(url, width, height, fps, backend=backend)
                # Logger.debug(url, "MediaStream")

            if endpoint is not None and stream.captured:
                StreamingServer.endpointAdd(endpoint, stream)

        # stream.capture()
        return stream

    def pause(self, url: str) -> None:
        if (stream := StreamManager.STREAM.get(url, None)) is None:
            return
        stream.pause()

# =============================================================================
# === SERVER ===
# =============================================================================

class StreamingHandler(BaseHTTPRequestHandler):
    def __init__(self, outputs, *arg, **kw) -> None:
        self.__outputs = outputs
        super().__init__(*arg, **kw)

    def do_GET(self) -> None:
        key = self.path.lower()

        # Check if the key exists in your data dictionary
        if key in self.__outputs:
            data = self.__outputs[key]

            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()

            while True:
                try:
                    if (frame := data['b']) is not None:
                        _, jpeg = cv2.imencode('.jpg', frame)
                        self.wfile.write(b'--frame\r\n')
                        self.send_header('Content-Type', 'image/jpeg')
                        self.send_header('Content-Length', len(jpeg))
                        self.end_headers()
                        self.wfile.write(jpeg.tobytes())
                        self.wfile.write(b'\r\n')
                except Exception as e:
                    Logger.err(f"Error: {e}")
                    break

        elif key == 'jovimetrix':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            data = json.dumps(data)
            self.wfile.write(data.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

class StreamingServer(metaclass=Singleton):
    OUT = {}

    @classmethod
    def endpointAdd(cls, name: str, stream: MediaStreamDevice) -> None:
        StreamingServer.OUT[name] = {'_': stream, 'b': None}
        Logger.debug(f"ENDPOINT_ADD ({name})")

    def __init__(self, host: str='', port: int=7227) -> None:
        self.__host = host
        self.__port = port
        self.__address = (self.__host, self.__port)
        self.__thread_server = threading.Thread(target=self.__server, daemon=True)
        self.__thread_server.start()
        self.__thread_capture = threading.Thread(target=self.__capture, daemon=True)
        self.__thread_capture.start()
        Logger.info("STARTED")

    def __server(self) -> None:
        httpd = ThreadingHTTPServer(self.__address, lambda *args: StreamingHandler(StreamingServer.OUT, *args))
        while True:
            httpd.handle_request()

    def __capture(self) -> None:
        while True:
            current = StreamingServer.OUT.copy()
            for k, v in current.items():
                if (device := v['_']) is not None:
                    _, frame = device.frame
                    StreamingServer.OUT[k]['b'] = frame

def __getattr__(name: str) -> Any:
    if name == "StreamManager":
        return StreamManager()
    elif name == "StreamingServer":
        return StreamingServer()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# =============================================================================
# === TESTING ===
# =============================================================================

def streamReadTest() -> None:
    urls = [
        0,1,
        "http://63.142.183.154:6103/mjpg/video.mjpg",
        "http://104.207.27.126:8080/mjpg/video.mjpg",
        "http://185.133.99.214:8011/mjpg/video.mjpg",
        "http://tapioles.eu:85/mjpg/video.mjpg",
        "http://63.142.190.238:6106/mjpg/video.mjpg",
        "http://77.222.181.11:8080/mjpg/video.mjpg",
        "http://195.196.36.242/mjpg/video.mjpg",
        "http://honjin1.miemasu.net/nphMotionJpeg?Resolution=320x240&Quality=Standard",
        "http://clausenrc5.viewnetcam.com:50003/nphMotionJpeg?Resolution=320x240&Quality=Standard",
        "http://takemotopiano.aa1.netvolante.jp:8190/nphMotionJpeg?Resolution=320x240&Quality=Standard",
        "http://tamperehacklab.tunk.org:38001/nphMotionJpeg?Resolution=320x240&Quality=Standard",
        "http://vetter.viewnetcam.com:50000/nphMotionJpeg?Resolution=320x240&Quality=Standard",
        "http://61.211.241.239/nphMotionJpeg?Resolution=320x240&Quality=Standard",
        "http://webcam.mchcares.com/mjpg/video.mjpg",
        "http://htadmcam01.larimer.org/mjpg/video.mjpg",
        "http://pendelcam.kip.uni-heidelberg.de/mjpg/video.mjpg",
        "https://gbpvcam01.taferresorts.com/mjpg/video.mjpg",
        "http://217.147.30.197:8087/mjpg/video.mjpg",
    ]
    streamIdx = 0

    widthT = 240
    heightT = 160

    empty = np.zeros((heightT, widthT, 3), dtype=np.uint8)
    try:
        StreamManager().capture(urls[streamIdx % len(urls)], widthT, heightT)
    except Exception as e:
        Logger.err(e)
    streamIdx += 1

    while True:
        streams = []
        for x in StreamManager().active:
            ret, chunk = x.frame
            if not ret or chunk is None:
                chunk = np.zeros((heightT, widthT, 3), dtype=np.uint8)
            else:
                chunk = cv2.resize(chunk, (widthT, heightT))
            streams.append(chunk)

        if len(streams) > 0:
            frame = image_grid(streams, widthT, heightT)
        else:
            frame = empty

        try:
            cv2.imshow("Media", frame)
        except Exception as e:
            Logger.err(e)
        val = cv2.waitKey(1) & 0xFF
        if val == ord('c'):
            try:
                StreamManager().capture(urls[streamIdx % len(urls)], widthT, heightT)
            except Exception as e:
                Logger.err(e)
            streamIdx += 1
        elif val == ord('q'):
            break

    cv2.destroyAllWindows()

def streamWriteTest() -> None:
    Logger.debug(cv2.getBuildInformation())
    ss = StreamingServer()

    fpath = 'res/stream-video.mp4'
    try:
        device = StreamManager().capture(fpath, 96, 54, endpoint=f'/media')
        device.fps = 30
    except:
        pass

    try:
        StreamManager().capture(0, 72, 32, endpoint='/stream/0')
    except:
        pass

    try:
        StreamManager().capture(1, endpoint='/stream/1')
    except:
        pass

    while 1:
        pass

if __name__ == "__main__":
    streamReadTest()
    # streamWriteTest()
