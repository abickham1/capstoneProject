from flask import Flask, render_template, request, redirect, url_for, flash

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

        flash("Login successful!", "success")
        return redirect(url_for("index"))

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

# ----------------- Run -----------------
if __name__ == "__main__":
    app.run(debug=True)
