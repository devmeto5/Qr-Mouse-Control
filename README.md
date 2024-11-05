# Mouse Control via QR Code - Step-by-Step Instructions

This README provides detailed instructions on how to set up and use a script that allows you to control your computer's mouse using your phone by scanning a QR code.

## Requirements

- Python 3 installed on your computer
- A local network that connects both your phone and computer

## Step 1: Install Required Libraries

Open your terminal or command prompt and install the required Python libraries:

```bash
pip install Flask pyautogui qrcode
```

These libraries are needed to create the web server (`Flask`), control the mouse (`pyautogui`), and generate a QR code (`qrcode`).

## Step 2: Create the Python Script

Create a new file called `mouse_control_server.py` and copy the following script into it:

```python
import pyautogui
from flask import Flask, request, jsonify, render_template_string
import qrcode
import socket
from collections import deque

# Get the computer's IP address
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

# Create the Flask server
app = Flask(__name__)

# Queue to store recent cursor movements (for smoothing)
movement_history = deque(maxlen=5)

# HTML template for controlling the mouse
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mouse Control</title>
    <style>
        body {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            background-color: #f0f0f0;
            margin: 0;
        }
        #touchpad {
            width: 300px;
            height: 300px;
            border: 1px solid black;
            background-color: #d3d3d3;
            touch-action: none;
            margin-bottom: 20px;
        }
        .button-container {
            display: flex;
            gap: 20px;
        }
        .button-left {
            width: 400px;
            height: 200px;
            background-color: green;
            border: none;
            border-radius: 10px;
        }
        .button-right {
            width: 400px;
            height: 200px;
            background-color: red;
            border: none;
            border-radius: 10px;
        }
    </style>
</head>
<body>
    <h1>Mouse Control</h1>
    <div id="touchpad"></div>
    <div class="button-container">
        <button class="button-left" onclick="sendClick('left')"></button>
        <button class="button-right" onclick="sendClick('right')"></button>
    </div>
    <script>
        let lastX = null;
        let lastY = null;
        let touchpad = document.getElementById('touchpad');

        touchpad.addEventListener('touchstart', function(event) {
            let touch = event.touches[0];
            lastX = touch.clientX;
            lastY = touch.clientY;
        });

        touchpad.addEventListener('touchmove', function(event) {
            event.preventDefault();
            let touch = event.touches[0];
            if (lastX !== null && lastY !== null) {
                let deltaX = (touch.clientX - lastX) * 2;  // Increase movement step
                let deltaY = (touch.clientY - lastY) * 2;
                
                // Send cursor movement data to the server
                fetch('/move', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ dx: deltaX, dy: deltaY })
                }).then(response => response.json())
                .then(data => console.log(data))
                .catch(error => console.error('Error:', error));

                lastX = touch.clientX;
                lastY = touch.clientY;
            }
        });

        touchpad.addEventListener('touchend', function() {
            lastX = null;
            lastY = null;
        });

        function sendClick(button) {
            fetch('/click', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ button: button })
            }).then(response => response.json())
            .then(data => console.log(data))
            .catch(error => console.error('Error:', error));
        }
    </script>
</body>
</html>
'''

# Route to display the web interface
@app.route('/')
def index():
    return render_template_string(html_template)

# Handle cursor movement
@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    if 'dx' in data and 'dy' in data:
        try:
            # Add the current movements to the queue for smoothing
            movement_history.append((data['dx'], data['dy']))
            
            # Calculate the average movement
            avg_dx = sum(m[0] for m in movement_history) / len(movement_history)
            avg_dy = sum(m[1] for m in movement_history) / len(movement_history)
            
            # Get the current cursor position
            x, y = pyautogui.position()
            new_x = x + avg_dx
            new_y = y + avg_dy
            print(f"Moving cursor to: x={new_x}, y={new_y}")
            pyautogui.moveTo(new_x, new_y, duration=0.05)  # Smooth movement with delay
            return jsonify({"status": "success"})
        except Exception as e:
            print(f"Error moving cursor: {e}")
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "Invalid data"})

# Handle mouse click
@app.route('/click', methods=['POST'])
def click():
    data = request.get_json()
    if 'button' in data:
        try:
            if data['button'] == 'left':
                pyautogui.click(button='left')
            elif data['button'] == 'right':
                pyautogui.click(button='right')
            return jsonify({"status": "success"})
        except Exception as e:
            print(f"Error clicking mouse: {e}")
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "Invalid data"})

if __name__ == '__main__':
    # Get the IP address and generate the QR code
    ip = get_ip()
    url = f'http://{ip}:5000'
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save("server_qr_code.png")
    print(f"Server started. Scan the QR code (server_qr_code.png) to connect.")

    # Start the Flask server
    app.run(host='0.0.0.0', port=5000)
```

## Step 3: Start the Server

Open your terminal, navigate to the directory where you saved `mouse_control_server.py`, and run the script:

```bash
python mouse_control_server.py
```

A QR code will be generated and saved as `server_qr_code.png`. This QR code contains a link to the web interface for controlling the mouse.

## Step 4: Connect Using Your Phone

1. Open a QR code scanner on your phone and scan the `server_qr_code.png` file.
2. The QR code will redirect you to a webpage (e.g., `http://<your-ip-address>:5000`).
3. Open the link in your phone's browser.

## Step 5: Control the Mouse

You can now use the interface on your phone to control the mouse cursor on your computer.

- **Touchpad**: Move your finger over the touchpad area to move the cursor.
- **Buttons**: Tap the left or right button to perform left or right mouse clicks.

## Troubleshooting

- Ensure your computer and phone are connected to the same local network.
- Ensure Python 3 and all required libraries are installed correctly.
- If the script fails to start, check for errors in the terminal output.

## Conclusion

With this setup, you can remotely control your computer's mouse using your phone. This simple project demonstrates how easily different devices can interact with each other over a local network.

