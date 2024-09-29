import argparse
import asyncio
import json
import logging
import os
import ssl

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer

ROOT = os.path.dirname(__file__)
pcs = set()  # To keep track of peer connections

async def index(request):
    # Serve the HTML page
    return web.Response(content_type="text/html", text="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebRTC Simple Stream</title>
        <script>
            let pc;
            async function start() {
                pc = new RTCPeerConnection();
                
                // Create an offer and set it as the local description
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);

                // Send the offer to the server
                const response = await fetch("/offer", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ sdp: pc.localDescription.sdp, type: pc.localDescription.type })
                });

                const answer = await response.json();
                await pc.setRemoteDescription(new RTCSessionDescription(answer));

                pc.ontrack = (event) => {
                    const video = document.createElement("video");
                    video.srcObject = event.streams[0];
                    video.autoplay = true;
                    document.body.appendChild(video);
                };
            }
        </script>
    </head>
    <body>
        <h1>Start WebRTC Stream</h1>
        <button onclick="start()">Start Streaming</button>
    </body>
    </html>
    """)

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    # Open media source from the webcam
    player = MediaPlayer("/dev/video0")  # Adjust based on your platform
    await pc.setRemoteDescription(offer)
    
    for t in pc.getTransceivers():
        if t.kind == "video" and player.video:
            pc.addTrack(player.video)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})
    )

async def on_shutdown(app):
    # Close all peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WebRTC webcam demo")
    parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
    parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
    parser.add_argument("--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port for HTTP server (default: 8080)")
    args = parser.parse_args()

    if args.cert_file:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(args.cert_file, args.key_file)
    else:
        ssl_context = None

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_post("/offer", offer)
    web.run_app(app, host=args.host, port=args.port, ssl_context=ssl_context)
