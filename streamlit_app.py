import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
import cv2
import av
import logging

# Enable debug logging for streamlit-webrtc
logging.getLogger('streamlit-webrtc').setLevel(logging.DEBUG)

# Suppress unnecessary warnings (optional)
logging.getLogger("asyncio").setLevel(logging.ERROR)

# Streamlit sliders for Canny edge detection thresholds
st.sidebar.title("Canny Edge Detection Parameters")
th1 = st.sidebar.slider("Threshold1", 0, 500, 100)
th2 = st.sidebar.slider("Threshold2", 0, 500, 200)

# Define the Video Transformer using VideoTransformerBase
class CannyEdgeTransformer(VideoTransformerBase):
    def __init__(self):
        super().__init__()  # Call the base class constructor
        self.th1 = th1
        self.th2 = th2

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        # Update thresholds based on current slider values
        self.th1 = th1
        self.th2 = th2

        # Convert frame to numpy array
        img = frame.to_ndarray(format="bgr24")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian Blur to reduce noise (optional but recommended)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Apply Canny Edge Detection
        edges = cv2.Canny(blurred, self.th1, self.th2)

        # Convert single channel edge image back to BGR for display
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        # Create a new av.VideoFrame from the processed image
        frame_out = av.VideoFrame.from_ndarray(edges_colored, format="bgr24")

        return frame_out

# Initialize Streamlit app layout
st.title("Live Webcam Feed with Canny Edge Detection")
st.write("Adjust the sliders in the sidebar to change the Canny edge detection thresholds.")

# Configure WebRTC streamer
webrtc_streamer(
    key="canny-edge",
    mode=WebRtcMode.SENDRECV,  # Enable both sending and receiving video
    video_processor_factory=CannyEdgeTransformer,  # Pass the transformer class
    media_stream_constraints={"video": True, "audio": False},  # Enable video, disable audio
    async_processing=False,  # Enable asynchronous frame processing for better performance
)

# Display current threshold values
with st.sidebar:
    st.markdown(f"**Current Thresholds:**\n- Threshold1: {th1}\n- Threshold2: {th2}")
