# app.py
import os
import logging
from functools import wraps
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime

from flask import (
    Flask, request, jsonify, render_template, redirect, url_for, session,
    send_from_directory, Response
)

from models import UserManager, ResultStorage
from processing import DeepfakeDetectionEngine
from report_utils import generate_pdf_report

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024
SECRET_KEY = os.urandom(24)
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = 'Lax'

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(module)s:%(funcName)s:%(lineno)d: %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = SESSION_COOKIE_SECURE
app.config['SESSION_COOKIE_SAMESITE'] = SESSION_COOKIE_SAMESITE

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'frames')):
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'frames'))

user_manager = UserManager()
result_storage = ResultStorage()
detection_engine = DeepfakeDetectionEngine(upload_folder_base=app.config['UPLOAD_FOLDER'])

@app.template_filter('format_datetime')
def format_datetime_filter(s):
    if isinstance(s, (int, float)):
        try:
            return datetime.fromtimestamp(s).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return "Invalid Date"
    return s

@app.context_processor
def inject_year():
    return {'year': datetime.utcnow().year}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.info("Login required, redirecting to login page.")
            return redirect(url_for('login_page', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page', next=request.url))
        user = user_manager.get_user_by_id(session['user_id'])
        if not user or not user.is_admin:
            logger.warning(f"Admin access denied for user: {session.get('username')}")
            return redirect(url_for('home_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index_redirect():
    if 'user_id' in session:
        return redirect(url_for('home_page'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if 'user_id' in session:
        return redirect(url_for('home_page'))
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({"success": False, "message": "Username and password required."}), 400

        user = user_manager.get_user_by_username(username)
        if user and user.check_password(password):
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            logger.info(f"User '{username}' logged in successfully.")
            return jsonify({"success": True, "message": "Login successful."})
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return jsonify({"success": False, "message": "Invalid credentials."}), 401
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if 'user_id' in session:
        return redirect(url_for('home_page'))
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({"success": False, "message": "Username and password required."}), 400
        if len(password) < 6:
             return jsonify({"success": False, "message": "Password must be at least 6 characters."}), 400

        user = user_manager.add_user(username, password)
        if user:
            return jsonify({"success": True, "message": "Signup successful. Please login."})
        else:
            return jsonify({"success": False, "message": "Username already exists or error."}), 409
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logger.info(f"User '{session.get('username')}' logged out.")
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/home')
@login_required
def home_page():
    return render_template('home.html')

@app.route('/detect')
@login_required
def detect_page():
    return render_template('detect.html')

@app.route('/analyze_video', methods=['POST'])
@login_required
def analyze_video_route():
    if 'videoFile' not in request.files:
        logger.warning("Analyze attempt with no video file part.")
        return jsonify({"success": False, "message": "No video file part."}), 400
    file = request.files['videoFile']

    is_valid, msg = detection_engine.video_processor.validate_video_file(file)
    if not is_valid:
        logger.warning(f"Invalid video file uploaded: {msg}")
        return jsonify({"success": False, "message": msg}), 400

    temp_video_path = None
    try:
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        temp_video_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(temp_video_path)
        logger.info(f"Video '{filename}' (saved as {unique_filename}) for analysis by {session.get('username')}.")

        analysis_result = detection_engine.analyze_video(temp_video_path, filename)

        if analysis_result.get("success"):
            result_id = result_storage.save_result(session['user_id'], analysis_result)
            analysis_result['result_id'] = result_id
            return jsonify(analysis_result)
        else:
            return jsonify(analysis_result), 500

    except Exception as e:
        logger.exception(f"Critical error during video analysis for user {session.get('username')}:")
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
                logger.info(f"Cleaned up {temp_video_path} after exception.")
            except OSError as del_e:
                 logger.error(f"Error deleting temp file {temp_video_path} during exception handling: {del_e}")
        return jsonify({"success": False, "message": f"An internal server error occurred."}), 500

@app.route('/report')
@login_required
def report_page():
    return render_template('report.html')

@app.route('/download_report_pdf', methods=['POST'])
@login_required
def download_report_pdf():
    try:
        analysis_data = request.get_json()
        if not analysis_data:
            return jsonify({"error": "No analysis data provided"}), 400

        report_user_id = analysis_data.get('user_id')
        is_owner = report_user_id == session['user_id']
        is_admin_session = session.get('is_admin', False)

        if not (is_owner or is_admin_session):
            logger.warning(f"User {session['username']} ({session['user_id']}) attempted to download report for user {report_user_id} without admin rights.")
            return jsonify({"error": "Access denied to this report."}), 403

        pdf_bytes = generate_pdf_report(analysis_data)
        video_filename = analysis_data.get("filename", "video_file").split('.')[0]
        pdf_filename = f"DeepFake_Analysis_Report_{secure_filename(video_filename)}.pdf"

        logger.info(f"Generated PDF report for {video_filename} for user {session.get('username')}")
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment;filename={pdf_filename}'}
        )
    except Exception as e:
        logger.exception("Error generating PDF report:")
        return jsonify({"error": f"Failed to generate PDF report."}), 500

@app.route('/history')
@login_required
def history_page():
    user_results = result_storage.get_results_by_user(session['user_id'])
    return render_template('history.html', results=user_results)

@app.route('/view_report/<result_id>')
@login_required
def view_specific_report_page(result_id):
    result_data = result_storage.get_result(result_id)
    if not result_data:
        logger.warning(f"User {session.get('username')} attempted to access non-existent report {result_id}")
        return "Report not found.", 404
    
    if result_data['user_id'] != session['user_id'] and not session.get('is_admin'):
        logger.warning(f"User {session.get('username')} attempted to access unauthorized report {result_id} belonging to {result_data['user_id']}")
        return "Access denied to this report.", 403
        
    if session.get('is_admin') and result_data['user_id'] != session['user_id']:
        owner = user_manager.get_user_by_id(result_data['user_id'])
        result_data['owner_username'] = owner.username if owner else "Unknown Owner"

    return render_template('report.html', analysis_result_data=result_data)

@app.route('/update_password', methods=['GET', 'POST'])
@login_required
def update_password_page():
    if request.method == 'POST':
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return jsonify({"success": False, "message": "All fields are required."}), 400
        if len(new_password) < 6:
             return jsonify({"success": False, "message": "New password must be at least 6 characters."}), 400

        user = user_manager.get_user_by_id(session['user_id'])
        if user and user.check_password(current_password):
            user_manager.update_password(user.username, new_password)
            return jsonify({"success": True, "message": "Password updated successfully."})
        else:
            return jsonify({"success": False, "message": "Incorrect current password."}), 401
    return render_template('update_password.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard_page():
    return render_template('admin_dashboard.html')

@app.route('/admin/users')
@admin_required
def admin_users_page():
    all_users = user_manager.get_all_users()
    return render_template('admin_users.html', users=all_users)

@app.route('/admin/users/delete/<user_id_to_delete>', methods=['POST'])
@admin_required
def admin_delete_user(user_id_to_delete):
    user_to_delete = user_manager.get_user_by_id(user_id_to_delete)
    if not user_to_delete:
        return jsonify({"success": False, "message": "User not found."}), 404
    if user_to_delete.username == "admin":
         return jsonify({"success": False, "message": "Cannot delete primary admin account."}), 403

    if user_manager.delete_user(user_to_delete.username):
        return jsonify({"success": True, "message": f"User '{user_to_delete.username}' deleted."})
    else:
        return jsonify({"success": False, "message": "Failed to delete user."}), 500

@app.route('/admin/users/reset_password/<user_id_to_reset>', methods=['POST'])
@admin_required
def admin_reset_password(user_id_to_reset):
    user_to_reset = user_manager.get_user_by_id(user_id_to_reset)
    if not user_to_reset:
        return jsonify({"success": False, "message": "User not found."}), 404

    new_temp_password = "Password123!"
    if user_manager.update_password(user_to_reset.username, new_temp_password):
        logger.info(f"Admin '{session.get('username')}' reset password for '{user_to_reset.username}'. New temp pass: {new_temp_password}")
        return jsonify({"success": True, "message": f"Password for '{user_to_reset.username}' reset. Temporary password: '{new_temp_password}'. User should change it immediately."})
    else:
        return jsonify({"success": False, "message": "Failed to reset password."}), 500

@app.route('/admin/results')
@admin_required
def admin_all_results_page():
    all_results = result_storage.get_all_results()
    for res in all_results:
        user = user_manager.get_user_by_id(res['user_id'])
        res['username'] = user.username if user else "Unknown User"
    return render_template('admin_all_results.html', results=all_results)

@app.route('/uploads/frames/<filename>')
@login_required
def uploaded_frame(filename):
    safe_filename = secure_filename(filename)
    if ".." in safe_filename or safe_filename.startswith("/"):
        logger.warning(f"Potential directory traversal attempt for frame: {filename}")
        return "Invalid filename", 400
    
    frames_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'frames')
    return send_from_directory(frames_dir, safe_filename)

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

if __name__ == '__main__':
    logger.info("Starting DeepGuard Detection System (Modularized)...")
    app.run(host='0.0.0.0', port=5000, debug=False)