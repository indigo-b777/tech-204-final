from flask import Flask, request, jsonify
from flask_cors import CORS
from pythonosc import udp_client
import os
import base64
import time
import random

app = Flask(__name__)
CORS(app)  # Allow requests from your phone/browser

# TouchDesigner OSC client (set to your local TouchDesigner IP and port)
osc_ip = "127.0.0.1"
osc_port = 8000  # make sure this matches your OSC In CHOP port
client = udp_client.SimpleUDPClient(osc_ip, osc_port)

# Folder to save images
SAVE_FOLDER = "received_photos"
os.makedirs(SAVE_FOLDER, exist_ok=True)

# Helper function to fix the base64 padding issue
def pad_base64(b64_string):
    return b64_string + '=' * (-len(b64_string) % 4)

@app.route("/upload", methods=["POST"])
def upload():
    data = request.get_json()

    # Grab image data from JSON
    img_data = data.get("image")
    if not img_data:
        return jsonify({"error": "No image provided"}), 400

    # Remove any metadata (like 'data:image/jpeg;base64,') and fix padding
    b64_str = img_data.split(",")[1]
    b64_str = pad_base64(b64_str)  # Add padding to ensure the base64 is correct
    
    # Decode base64 image
    try:
        img_bytes = base64.b64decode(b64_str)
    except Exception as e:
        return jsonify({"error": f"Failed to decode image: {str(e)}"}), 500

    # Save image to file
    timestamp = int(time.time())
    unique_suffix = random.randint(1000, 9999)  # Add random component to avoid filename collision
    filename = f"photo_{timestamp}_{unique_suffix}.jpg"
    filepath = os.path.join(SAVE_FOLDER, filename)
    
    try:
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        print(f"[+] Saved image: {filename}")
    except Exception as e:
        return jsonify({"error": f"Failed to save image: {str(e)}"}), 500

    # Send OSC message to TouchDesigner
    try:
        client.send_message("/photo", 1)  # change address as needed in TD
        print("[+] Sent OSC trigger to TouchDesigner")
    except Exception as e:
        return jsonify({"error": f"Failed to send OSC message: {str(e)}"}), 500

    return jsonify({"status": "success", "file": filename})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
