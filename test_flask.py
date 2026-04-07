import os
import random
from flask import Flask, render_template, request, redirect, url_for, flash, session
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.efficientnet import preprocess_input
from datetime import timedelta
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
    img_array = preprocess_input(img_array)
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

        session["username"] = username
        session.permanent = True
        app.permanent_session_lifetime = timedelta(days=1)

        return redirect(url_for("main"))

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

        session["username"] = username

        remember = request.form.get("remember") 
        if remember == "yes":
            session.permanent = True
            app.permanent_session_lifetime = timedelta(days=30)
        else:
            session.permanent = False  # expires when browser closes

        #flash("Login successful!", "success")
        return redirect(url_for("main"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Logged out successfully", "success")
    return redirect(url_for("index"))

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

@app.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    if request.method == "POST":
        if "username" in session:
            username = session["username"]
            users.pop(username, None)
            session.clear()
            flash("Your account has been deleted.", "success")
            return redirect(url_for("index"))

    return render_template("delete_account.html")

@app.route("/edit_username", methods=["GET", "POST"])
def edit_username():
    if "username" not in session:
        flash("You must be logged in to edit your username.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        new_username = request.form.get("edit_username", "").strip()
        current_username = session["username"]

        if not new_username:
            flash("Please enter a valid username.", "error")
            return redirect(url_for("edit_username"))

        if username_exists(new_username):
            flash("This username is already taken.", "error")
            return redirect(url_for("edit_username"))

        # Update database
        users[new_username] = users.pop(current_username)

        # Update session
        session["username"] = new_username

        flash(f"Username updated successfully to {new_username}!", "success")
        return redirect(url_for("profile"))

    return render_template("edit_username.html")

@app.route("/update_password", methods=["GET", "POST"])
def update_password():
    if "username" not in session:
        flash("You must be logged in to update your password.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        username = session["username"]

        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # Check current password
        if users[username]["password"] != current_password:
            flash("Current password is incorrect.", "error")
            return redirect(url_for("update_password"))

        # Check match
        if new_password != confirm_password:
            flash("New password and confirmation do not match.", "error")
            return redirect(url_for("update_password"))

        # Validate password
        errors = validate_password(new_password)
        if errors:
            flash(" | ".join(errors), "error")
            return redirect(url_for("update_password"))

        # Update password
        users[username]["password"] = new_password
        flash("Password updated successfully!", "success")
        return redirect(url_for("profile"))

    # GET request → show page
    return render_template("update_password.html")

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
    result = None

    if not IMAGES:
        return "No images available" 
    
    if "history" not in session:
        session["history"] = []
        session["current_index"] = -1 # start at -1 so first right click goes to index 0
        session["score"] = 0
        session["attempts"] = 0

    history = session["history"]
    current_index = session.get("current_index", -1)

    #favorites
    if "favorites" not in session:
        session["favorites"] = []

    if request.method == "POST" and "favorite" in request.form:
        img_file = history[current_index]

        favorites = session["favorites"]

        if img_file not in favorites:
            favorites.append(img_file)

        session["favorites"] = favorites

    if current_index == -1:
        # First image
        img_file = get_random_image()
        history.append(img_file)
        current_index = 0
        session["history"] = history
        session["current_index"] = current_index
    else:
        img_file = history[current_index]

    img_full_path = os.path.join(STATIC_IMAGE_PATH, img_file)

    if request.method == "POST" and "classification" in request.form:
        user_choice = request.form["classification"]
        pred_class, pred_conf = predict_image(img_full_path)

        session["attempts"] = session.get("attempts", 0) + 1
        is_correct = user_choice == pred_class

        if is_correct:
            if session["attempts"] == 1:
                session["score"] = session.get("score", 0) + 3
            elif session["attempts"] == 2:
                session["score"] = session.get("score", 0) + 2
            else:
                session["score"] = session.get("score", 0) + 1

        result = {
            "selected": user_choice,
            "correct_answer": pred_class,
            "is_correct": is_correct,
            "attempts": session["attempts"],
            "score": session.get("score", 0)
        }

        if is_correct:
            new_img = get_random_image()
            history.append(new_img)
            current_index += 1
            session["history"] = history
            session["current_index"] = current_index
            session["attempts"] = 0  # reset attempts for next image
            img_file = new_img  # display next image
            result = None 

    direction = request.values.get("direction")
    if direction == "left" and current_index > 0:
        current_index -= 1
        session["current_index"] = current_index
        session["attempts"] = 0  # reset attempts for previous image
        img_file = history[current_index]
        result = None

    img_rel_path = f"data/galaxy-zoo/images_gz2/images/{img_file}"

    return render_template(
        "examinations.html",img_path=img_rel_path,class_names=class_names,result=result,score=session.get("score", 0)
    )

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/favorites", methods=["GET", "POST"])
def favorites():
    if "favorites" not in session:
        session["favorites"] = []

    favorites = session["favorites"]

    if request.method == "POST":
        img_to_remove = request.form.get("remove_image")

        if img_to_remove and img_to_remove in favorites:
            favorites.remove(img_to_remove)
            session["favorites"] = favorites
            flash("Removed from favorites.", "success")

        return redirect(url_for("favorites"))  # ✅ prevents refresh issues

    return render_template("favorites.html", favorites=favorites)

# ----------------- Run -----------------
if __name__ == "__main__":
    app.run(debug=True)
