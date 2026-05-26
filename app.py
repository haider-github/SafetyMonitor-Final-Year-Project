from flask import (Flask, render_template, Response, request,
                   redirect, url_for, jsonify, session)
from camera import VideoStream
from database import (init_db, get_all_violations, get_all_workers,
                      add_worker, get_violation_count, get_worker_count,
                      get_recent_violations, get_worker_by_id,
                      update_worker, delete_worker)
import sqlite3
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "safety_monitor_secret_2024"

os.makedirs("static/uploads",   exist_ok=True)
os.makedirs("static/snapshots", exist_ok=True)

init_db()
stream = VideoStream(source=0)

# ── Supervisor credentials ──
SUPERVISOR_USERNAME = "admin"
SUPERVISOR_PASSWORD = "admin123"

# ── Multiple cameras ──
cameras = {
    "0": stream,
    # "1": VideoStream(source=1),
}


# ── Login required decorator ──
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ── Auth ──
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if username == SUPERVISOR_USERNAME and password == SUPERVISOR_PASSWORD:
            session['logged_in'] = True
            session['username']  = username
            return redirect(url_for('index'))
        else:
            error = "Invalid username or password. Please try again."
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── Dashboard ──
@app.route('/')
@login_required
def index():
    violations       = get_recent_violations(10)
    total_violations = get_violation_count()
    total_workers    = get_worker_count()
    return render_template('index.html',
                           violations=violations,
                           total_violations=total_violations,
                           total_workers=total_workers)


# ── Video feeds ──
@app.route('/video_feed')
@login_required
def video_feed():
    return Response(stream.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed/<cam_id>')
@login_required
def video_feed_cam(cam_id):
    cam = cameras.get(cam_id, stream)
    return Response(cam.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# ── Camera view ──
@app.route('/camera/<cam_id>')
@login_required
def camera_view(cam_id):
    return render_template('camera.html',
                           cam_id=cam_id,
                           cameras=cameras)


# ── Violations ──
@app.route('/violations')
@login_required
def violations():
    data = get_all_violations()
    return render_template('violations.html', violations=data)


# ── Workers ──
@app.route('/workers', methods=['GET', 'POST'])
@login_required
def workers():
    message  = ""
    msg_type = "success"
    if request.method == 'POST':
        worker_id  = request.form['worker_id'].strip()
        name       = request.form['name'].strip()
        phone      = request.form['phone'].strip()
        department = request.form['department'].strip()
        location   = request.form['location'].strip()
        image      = request.files.get('image')
        image_path = ""
        if image and image.filename != "":
            image_path = f"static/uploads/{worker_id}_{image.filename}"
            image.save(image_path)
        result = add_worker(worker_id, name, phone,
                            department, location, image_path)
        if result == "success":
            stream.retrain()
            message  = "Worker added successfully!"
            msg_type = "success"
        else:
            message  = "Worker ID already exists!"
            msg_type = "danger"
    all_workers = get_all_workers()
    return render_template('workers.html',
                           workers=all_workers,
                           message=message,
                           msg_type=msg_type)


# ── Edit worker ──
@app.route('/edit_worker/<worker_id>', methods=['GET', 'POST'])
@login_required
def edit_worker(worker_id):
    worker = get_worker_by_id(worker_id)
    if request.method == 'POST':
        name       = request.form['name'].strip()
        phone      = request.form['phone'].strip()
        department = request.form['department'].strip()
        location   = request.form['location'].strip()
        image      = request.files.get('image')
        image_path = None
        if image and image.filename != "":
            image_path = f"static/uploads/{worker_id}_{image.filename}"
            image.save(image_path)
        update_worker(worker_id, name, phone,
                      department, location, image_path)
        stream.retrain()
        return redirect(url_for('workers'))
    return render_template('edit_worker.html', worker=worker)


# ── Delete worker ──
@app.route('/delete_worker/<worker_id>', methods=['POST'])
@login_required
def delete_worker_route(worker_id):
    delete_worker(worker_id)
    stream.retrain()
    return redirect(url_for('workers'))


# ── Retrain ──
@app.route('/retrain', methods=['POST'])
@login_required
def retrain():
    stream.retrain()
    return redirect(url_for('workers'))


# ── Worker report ──
@app.route('/worker_report/<worker_id>')
@login_required
def worker_report(worker_id):
    worker = get_worker_by_id(worker_id)
    conn   = sqlite3.connect('safety.db')
    viols  = conn.execute(
        "SELECT * FROM violations WHERE worker_id=? ORDER BY id DESC",
        (worker_id,)
    ).fetchall()
    conn.close()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template('worker_report.html',
                           worker=worker,
                           violations=viols,
                           now=now)


# ── API ──
@app.route('/api/recent_violations')
@login_required
def recent_violations_api():
    data   = get_recent_violations(5)
    result = []
    for v in data:
        result.append({
            "id":           v[0],
            "worker_id":    v[1],
            "missing_gear": v[2],
            "timestamp":    v[3],
            "worker_name":  v[5] or "Unknown",
            "department":   v[6] or "—",
            "phone":        v[7] or "—"
        })
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)