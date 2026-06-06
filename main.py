import os
import requests
from flask import Flask, jsonify, request, render_template, redirect, session
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(32).hex()

ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASS = os.environ["ADMIN_PASS"]

CF_EMAIL = os.environ["CF_EMAIL"]
CF_KEY = os.environ["CF_KEY"]
CF_ZONE_ID = os.environ["CF_ZONE_ID"]
CF_BASE = "https://api.cloudflare.com/client/v4"

HEADERS = {
    "X-Auth-Email": CF_EMAIL,
    "X-Auth-Key": CF_KEY,
    "Content-Type": "application/json",
}

def cf_get(path):
    return requests.get(f"{CF_BASE}{path}", headers=HEADERS).json()

def cf_post(path, data):
    return requests.post(f"{CF_BASE}{path}", headers=HEADERS, json=data).json()

def cf_delete(path):
    return requests.delete(f"{CF_BASE}{path}", headers=HEADERS).json()

def cf_patch(path, data):
    return requests.patch(f"{CF_BASE}{path}", headers=HEADERS, json=data).json()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        if email == ADMIN_EMAIL and password == ADMIN_PASS:
            session["logged_in"] = True
            return redirect("/")
        return render_template("login.html", error="Email atau password salah")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/api/records")
@login_required
def get_records():
    data = cf_get(f"/zones/{CF_ZONE_ID}/dns_records?per_page=100")
    return jsonify(data)

@app.route("/api/records", methods=["POST"])
@login_required
def add_record():
    body = request.json
    data = cf_post(f"/zones/{CF_ZONE_ID}/dns_records", {
        "type": body["type"],
        "name": body["name"].strip(),
        "content": body["content"].strip(),
        "ttl": 1,
        "proxied": body.get("proxied", True),
    })
    return jsonify(data)

@app.route("/api/records/<record_id>", methods=["DELETE"])
@login_required
def delete_record(record_id):
    data = cf_delete(f"/zones/{CF_ZONE_ID}/dns_records/{record_id}")
    return jsonify(data)

@app.route("/api/records/<record_id>", methods=["PATCH"])
@login_required
def update_record(record_id):
    body = request.json
    data = cf_patch(f"/zones/{CF_ZONE_ID}/dns_records/{record_id}", {
        "type": body["type"],
        "name": body["name"],
        "content": body["content"],
        "ttl": 1,
        "proxied": body.get("proxied", True),
    })
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
