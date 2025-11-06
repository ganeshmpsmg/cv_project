import os
import numpy as np
from flask import Flask, request, render_template_string, redirect, url_for, session
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
# ------------------------------
# 1️⃣ Flask App Setup
# ------------------------------
app = Flask(__name__)
app.secret_key = "secret123"  # For session security
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------------------
# 2️⃣ Load Pretrained Model
# ------------------------------
print("🔹 Loading pretrained MobileNetV2 model (ImageNet)...")
model = MobileNetV2(weights='imagenet')
print("✅ Model loaded successfully!")

# ------------------------------
# 3️⃣ HTML Templates
# ------------------------------

LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - Image AI App</title>
    <style>
        body { font-family: Arial; background: linear-gradient(to right, #6a11cb, #2575fc); color: white; }
        .login-box { background: rgba(255,255,255,0.1); padding: 50px; border-radius: 20px; width: 400px;
                     text-align: center; margin: 100px auto; box-shadow: 0 0 20px rgba(0,0,0,0.3); }
        input { width: 80%; padding: 10px; margin: 10px; border-radius: 10px; border: none; font-size: 18px; }
        button { background: #ff9800; color: white; border: none; padding: 15px 40px;
                 font-size: 20px; border-radius: 10px; cursor: pointer; transition: 0.3s; }
        button:hover { background: #ffc107; }
        h2 { margin-bottom: 30px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🔒 Login to Continue</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Enter Username" required><br>
            <input type="password" name="password" placeholder="Enter Password" required><br>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Image AI App</title>
    <style>
        body { font-family: Arial; background: linear-gradient(to right, #00c6ff, #0072ff); color: white; }
        .container { text-align: center; margin-top: 80px; }
        h1 { font-size: 45px; margin-bottom: 30px; }
        .button-block { display: flex; justify-content: center; gap: 30px; margin-top: 50px; flex-wrap: wrap; }
        .option-btn { background: #ff4081; color: white; border: none; padding: 25px 50px;
                      border-radius: 20px; font-size: 22px; cursor: pointer; box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                      transition: 0.3s; width: 250px; }
        .option-btn:hover { background: #f50057; transform: scale(1.05); }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Welcome, {{ username }}!</h1>
        <div class="button-block">
            <form action="/upload"><button class="option-btn">📸 Upload & Analyze Image</button></form>
            <form action="/about"><button class="option-btn">ℹ️ About App</button></form>
            <form action="/logout"><button class="option-btn">🚪 Logout</button></form>
        </div>
    </div>
</body>
</html>
"""

UPLOAD_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Upload Image</title>
    <style>
        body { font-family: Arial; background: #f4f4f4; text-align: center; }
        .container { background: white; margin: 60px auto; padding: 40px; width: 60%;
                     border-radius: 20px; box-shadow: 0 0 20px #aaa; }
        input[type=file] { margin: 20px; font-size: 18px; }
        input[type=submit] { background: #007BFF; color: white; border: none; padding: 15px 40px;
                             font-size: 20px; border-radius: 15px; cursor: pointer; }
        input[type=submit]:hover { background: #0056b3; }
        img { width: 350px; border-radius: 15px; margin-top: 25px; }
        .result { font-size: 24px; color: green; margin-top: 25px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Image Analyzer</h1>
        <p>Upload an image to get its prediction:</p>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" required><br>
            <input type="submit" value="Analyze">
        </form>
        {% if filename %}
            <img src="{{ url_for('static', filename='uploads/' + filename) }}" alt="Uploaded Image">
            <div class="result">
                <b>Prediction:</b> {{ label }} ({{ prob }}% confidence)
            </div>
        {% endif %}
        <br><br>
        <a href="/dashboard">⬅ Back to Dashboard</a>
    </div>
</body>
</html>
"""

ABOUT_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>About</title>
    <style>
        body { font-family: Arial; background: linear-gradient(to right, #ff9966, #ff5e62); color: white; text-align: center; padding: 50px; }
        .box { background: rgba(0,0,0,0.3); padding: 40px; border-radius: 20px; width: 60%; margin: auto; }
        h1 { margin-bottom: 30px; }
        a { color: yellow; font-size: 20px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>ℹ️ About This App</h1>
        <p>This web app uses a <b>pretrained MobileNetV2 deep learning model</b> to classify images into objects.</p>
        <p>Built using <b>Flask</b> + <b>TensorFlow Keras</b> with responsive UI.</p>
        <p>Creator: <b>Ganesh M P</b></p>
        <br>
        <a href="/dashboard">⬅ Back to Dashboard</a>
    </div>
</body>
</html>
"""

# ------------------------------
# 4️⃣ Routes
# ------------------------------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            return LOGIN_PAGE + "<p style='text-align:center;color:yellow;'>❌ Invalid login. Try again!</p>"
    return LOGIN_PAGE


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template_string(DASHBOARD_PAGE, username=session["username"])


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "username" not in session:
        return redirect(url_for("login"))

    label = None
    prob = None
    filename = None

    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            # Preprocess the image
            img = image.load_img(filepath, target_size=(224, 224))
            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            x = preprocess_input(x)

            preds = model.predict(x)
            decoded = decode_predictions(preds, top=1)[0][0]
            label, prob = decoded[1], round(decoded[2] * 100, 2)

            # Move file to static/uploads
            static_folder = os.path.join("static", "uploads")
            os.makedirs(static_folder, exist_ok=True)
            os.replace(filepath, os.path.join(static_folder, file.filename))

            return render_template_string(UPLOAD_PAGE, filename=file.filename, label=label, prob=prob)
    return render_template_string(UPLOAD_PAGE, filename=None)


@app.route("/about")
def about():
    if "username" not in session:
        return redirect(url_for("login"))
    return ABOUT_PAGE


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

# ------------------------------
# 5️⃣ Run the App
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
