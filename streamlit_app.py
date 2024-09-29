import asyncio
import cv2
import logging
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaStreamTrack
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
import av

# Enable debug logging for streamlit-webrtc
logging.getLogger('streamlit-webrtc').setLevel(logging.DEBUG)

# Suppress unnecessary warnings (optional)
logging.getLogger("asyncio").setLevel(logging.ERROR)

# Streamlit sliders for Canny edge detection thresholds
st.sidebar.title("Canny Edge Detection Parameters")
th1 = st.sidebar.slider("Threshold1", 0, 500, 100)
th2 = st.sidebar.slider("Threshold2", 0, 500, 200)

class VideoTransformTrack(MediaStreamTrack):
    def __init__(self):
        super().__init__()
        self.th1 = th1
        self.th2 = th2

    async def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian Blur to reduce noise (optional but recommended)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Apply Canny Edge Detection
        edges = cv2.Canny(blurred, self.th1, self.th2)

        # Convert single channel edge image back to BGR for display
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        return av.VideoFrame.from_ndarray(edges_colored, format="bgr24")

async def index(request):
    content = open("index.html", "r").read()
    return web.Response(content_type="text/html", text=content)

async def javascript(request):
    content = open("client.js", "r").read()
    return web.Response(content_type="application/javascript", text=content)

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        print("ICE connection state is %s" % pc.iceConnectionState)
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    # open media source
    player = VideoTransformTrack()

    await pc.setRemoteDescription(offer)
    for t in pc.getTransceivers():
        if t.kind == "video":
            pc.addTrack(player)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )

pcs = set()

async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

# Initialize Streamlit app layout
st.title("Live Webcam Feed with Canny Edge Detection")
st.write("Adjust the sliders in the sidebar to change the Canny edge detection thresholds.")

# Configure WebRTC streamer
webrtc_streamer(
    key="canny-edge",
    mode=WebRtcMode.SENDRECV,  # Enable both sending and receiving video
    video_processor_factory=VideoTransformTrack,  # Pass the transformer class
    media_stream_constraints={"video": True, "audio": False},  # Enable video, disable audio
    async_processing=True,  # Enable asynchronous frame processing for better performance
)

# Display current threshold values
st.sidebar.markdown(f"**Current Thresholds:**\n- Threshold1: {th1}\n- Threshold2: {th2}")
