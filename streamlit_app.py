import cv2
import numpy as np
import streamlit as st
from streamlit_webrtc import VideoTransformerBase, webrtc_streamer

# Create a class to process video frames
class VideoTransformer(VideoTransformerBase):
    def transform(self, frame):
        # Convert the frame to an OpenCV format
        img = frame.to_ndarray(format="bgr")

        # Apply Canny edge detection
        edges = cv2.Canny(img, 100, 200)

        # Convert back to the correct format for Streamlit
        return edges

# Set up the Streamlit app layout
st.title("WebRTC Canny Edge Detection")
st.write("This app uses WebRTC to stream video and apply Canny edge detection.")

# Start the WebRTC streamer with the custom transformer
webrtc_streamer(key="example", video_transformer_factory=VideoTransformer)
