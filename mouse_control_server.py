import pyautogui
from flask import Flask, request, jsonify, render_template_string
import qrcode
import socket
from collections import deque

# Определение IP-адреса компьютера
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

# Создание сервера Flask
app = Flask(__name__)

# Очередь для хранения последних перемещений курсора (для сглаживания)
movement_history = deque(maxlen=5)

# HTML-шаблон для управления курсором
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mouse Control</title>
    <style>
        #touchpad {
            width: 300px;
            height: 300px;
            border: 1px solid black;
            touch-action: none;
        }
        button {
            width: 100px;
            height: 50px;
            margin: 10px;
        }
    </style>
</head>
<body>
    <h1>Управление курсором</h1>
    <div id="touchpad"></div>
    <button onclick="sendClick('left')">Левая кнопка</button>
    <button onclick="sendClick('right')">Правая кнопка</button>
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
                let deltaX = (touch.clientX - lastX) * 2;  // Увеличение шага перемещения
                let deltaY = (touch.clientY - lastY) * 2;
                
                // Отправка данных о перемещении курсора на сервер
                fetch('/move', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ dx: deltaX, dy: deltaY })
                }).then(response => response.json())
                .then(data => console.log(data))
                .catch(error => console.error('Ошибка:', error));

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
            .catch(error => console.error('Ошибка:', error));
        }
    </script>
</body>
</html>
'''

# Маршрут для отображения веб-интерфейса
@app.route('/')
def index():
    return render_template_string(html_template)

# Управление курсором
@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    if 'dx' in data and 'dy' in data:
        try:
            # Добавляем текущие перемещения в очередь для сглаживания
            movement_history.append((data['dx'], data['dy']))
            
            # Вычисляем среднее значение перемещений
            avg_dx = sum(m[0] for m in movement_history) / len(movement_history)
            avg_dy = sum(m[1] for m in movement_history) / len(movement_history)
            
            # Получаем текущую позицию курсора
            x, y = pyautogui.position()
            new_x = x + avg_dx
            new_y = y + avg_dy
            print(f"Перемещение курсора: x={new_x}, y={new_y}")
            pyautogui.moveTo(new_x, new_y, duration=0.05)  # Плавное перемещение с задержкой
            return jsonify({"status": "success"})
        except Exception as e:
            print(f"Ошибка при перемещении курсора: {e}")
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "Invalid data"})

# Клик мыши
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
            print(f"Ошибка при клике мыши: {e}")
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "Invalid data"})

if __name__ == '__main__':
    # Определение IP-адреса и генерация QR-кода
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
    print(f"Сервер запущен. Сканируйте QR-код (server_qr_code.png), чтобы подключиться.")

    # Запуск сервера Flask
    app.run(host='0.0.0.0', port=5000)