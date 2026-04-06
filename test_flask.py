import os
import random
from flask import Flask, render_template, request, redirect, url_for, flash, session
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np

model = tf.keras.models.load_model("final_galaxy_classifier.keras")
class_names = ['elliptical', 'irregular', 'spiral']

app = Flask(__name__)
app.secret_key = "supersecretkey"  # needed for flash messages

# ----------------- Simulated Database -----------------
users = {}  # key=username, value=dict(email, password)

# ----------------- Password Validator -----------------
import re
def validate_password(password): 
    errors = []
    if len(password) < 8:
        errors.append("At least 8 characters")
    if " " in password:
        errors.append("No spaces allowed")
    if not re.search(r"[A-Z]", password):
        errors.append("One capital letter required")
    if not re.search(r"\d", password):
        errors.append("One number required")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("One symbol required")
    return errors

# ----------------- Helper Functions -----------------
def username_exists(username):
    return username in users

def email_exists(email):
    return any(user["email"] == email for user in users.values())

def prepare_image(img_path):
    img = image.load_img(img_path, target_size=(224, 224)) 
    img_array = image.img_to_array(img)
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def predict_image(img_path):
    img_array = prepare_image(img_path)
    predictions = model.predict(img_array)
    pred_class = class_names[np.argmax(predictions)]
    pred_conf = np.max(predictions) * 100
    return pred_class, pred_conf

# ----------------- Routes -----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]

        if email_exists(email):
            flash("Email already exists", "error")
            return redirect(url_for("signup"))
        if username_exists(username):
            flash("Username already exists", "error")
            return redirect(url_for("signup"))

        errors = validate_password(password)
        if errors:
            flash(" | ".join(errors), "error")
            return redirect(url_for("signup"))

        users[username] = {"email": email, "password": password}
        flash("Account created successfully!", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not username_exists(username):
            flash("Username does not exist", "error")
            return redirect(url_for("login"))

        if users[username]["password"] != password:
            flash("Password incorrect", "error")
            return redirect(url_for("login"))

        session["username"]= username
        flash("Login successful!", "success")
        return redirect(url_for("main"))

    return render_template("login.html")

@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        val = request.form["username_email"]
        if username_exists(val) or any(user["email"] == val for user in users.values()):
            flash("Password reset link sent (demo)", "success")
        else:
            flash("Username or email not found", "error")
        return redirect(url_for("forgot"))

    return render_template("forgot.html")

@app.route("/main")
def main():
    if "username" not in session:
        flash("Please log in to access the main menu", "error")
        return redirect(url_for("login"))
    return render_template("main.html")

@app.route("/community")
def community():
    return render_template("community.html")

STATIC_IMAGE_PATH = os.path.join('static', 'data', 'galaxy-zoo', 'images_gz2','images')

if os.path.exists(STATIC_IMAGE_PATH):
    IMAGES = sorted(os.listdir(STATIC_IMAGE_PATH))
else:
    IMAGES = []
    print(f"Warning: No images found at {STATIC_IMAGE_PATH}")

def get_random_image():
    last_image = session["history"][-1] if session.get("history") else None
    choices = [img for img in IMAGES if img != last_image]
    return random.choice(choices) if choices else last_image
    
@app.route("/examinations", methods=["GET", "POST"])
def examinations():
    if not IMAGES:
        return "No images available" 
    
    if "history" not in session:
        session["history"] = []

    history = session["history"]

    direction = request.values.get("direction", "right")

    if direction == "right":
        img_file = get_random_image()
        history.append(img_file) 

    elif direction == "left":
        if len(history) > 1:
            history.pop() 
            img_file = history[-1]  
        else:
            img_file = history[-1] if history else get_random_image()
            if not history:
                history.append(img_file)

    session["history"] = history
    img_rel_path = f"data/galaxy-zoo/images_gz2/images/{img_file}"
    img_full_path = os.path.join(STATIC_IMAGE_PATH, img_file)

    pred_class, pred_conf = predict_image(img_full_path)

    return render_template("examinations.html", img_path=img_rel_path, pred_class=pred_class, pred_conf=pred_conf)

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/favorites")
def favorites():
    return render_template("favorites.html")

# ----------------- Run -----------------
if __name__ == "__main__":
    app.run(debug=True)
