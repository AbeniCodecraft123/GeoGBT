# ALL THE SITE PACKAGES USED
from google import genai
import random
import datetime
import os
import atexit
import smtplib
from dotenv import load_dotenv
load_dotenv()
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import timedelta, datetime, timezone
from flask import (Flask, render_template, redirect, flash, url_for, session, request, jsonify,
                   current_app, Response)
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, UserMixin
from wtforms import StringField, PasswordField, SubmitField, EmailField, DateField, TextAreaField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Mail, Message
from flask_migrate import Migrate
from flask_dance.contrib.google import make_google_blueprint, google
# END OF THE SITE PACKAGES

# WEB APP CONFIGURATION
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT')
app.secret_key = os.getenv('CRSF_KEY')
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'abenicodecraft001@gmail.com'
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = 'aishat.jamb20@gmail.com'




# END OF WEB APP CONFIGURATION

# BINDING WEB APP
client = genai.Client(api_key=os.getenv("GEMINI_AI"))
mail = Mail(app)
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
migrate = Migrate(app, db)

google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    redirect_to="google_login"   # endpoint name
)

app.register_blueprint(google_bp, url_prefix="/login")

# END OF WEB APP BINDING


#CREATING TABLE FOR USER, AL TABLE USING OBJECT AND FLASK FORM


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)
    password = db.Column(db.String(255), nullable=True)
    google_id = db.Column(db.String(200), unique=True, nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    registered_on = db.Column(db.DateTime, default=datetime.utcnow)
    chats = db.relationship('Chat_table', backref='user', lazy=True)

    def __init__(self, full_name, email, password=None, google_id=None):
        self.full_name = full_name
        self.email = email
        if password:
            self.set_password(password)
        self.google_id = google_id

    def __repr__(self):
        return f"<User {self.full_name} | {self.email}>"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return self.password and check_password_hash(self.password, password)

    def obj_to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'password': self.password,
            'google_id': self.google_id,
            'registered_on': self.registered_on,

        }



class Signup(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password =PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match")
        ]
    )
    submit = SubmitField('Sign up')


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class Chat_table(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __init__(self, user_id, question, answer):
        self.user_id = user_id
        self.question = question
        self.answer = answer
        self.created_at = db.func.current_timestamp()

    def __repr__(self):
        return f"<Chat user_id={self.user_id}>"

    def obj_to_dict(self):
        return {
            'user_id': self.user_id,
            'question': self.question,
            'answer': self.answer,
            'created_at': self.created_at
        }

class Chats(FlaskForm):
      question= TextAreaField('Question', validators=[DataRequired()])
      answer = TextAreaField('Answer', validators=[DataRequired()])
      submit = SubmitField('Submit')


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Verification Code')


class VerifyCodeForm(FlaskForm):
    code = StringField('Verification Code', validators=[DataRequired(), Length(6,6)])
    submit = SubmitField('Verify Code')


class ResetPasswordForm(FlaskForm):
    email = EmailField('Email')
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

#END OF TABLE CREATION


# LOGIN CODES FOR USER SESSIONS


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
from werkzeug.security import generate_password_hash

# END OF LOGIN CODES FOR USER SESSIONS


# ALL THE FUNCTION FOR EMAIL VERIFICATION

def clear_old_chats():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    try:
        deleted = Chat_table.query.filter(Chat_table.created_at < cutoff).delete()
        db.session.commit()
        print(f"[Cleanup] Deleted {deleted} old chat(s).")
    except Exception as e:
        db.session.rollback()
        print(f"[Cleanup] Error deleting old chats: {e}")


def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def confirm_verification_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except SignatureExpired:
        return None
    except BadSignature:
        return None
    return email

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm', 'ogg'}



def send_verification_email(user):
    try:
        token = generate_verification_token(user.email)
        verify_url = url_for('verify_email', token=token, _external=True)

        msg = Message(
            "Verify Your Email - GeoGBT",
            sender=("GeoGBT", "aishat.jamb20@gmail.com"),
            recipients=[user.email]
        )
        msg.html = render_template(
            "admin/email_verification.html",
            user_name=user.full_name,
            verify_link=verify_url
        )

        mail.send(msg)
        return True  # ✅ email sent successfully

    except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
        # Log for you (optional, but recommended)
        print("Email sending failed:", e)

        # Friendly message for the user
        flash(
            "We couldn't send the verification email right now due to a network issue. "
            "Please try again later or check your internet connection.",
            "warning"
        )
        return False


# END OF EMAIL VERIFICATION CODES
DAILY_LIMIT = 13

# Start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=clear_old_chats, trigger="interval", hours=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())



@app.route("/google_login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info from Google.", "danger")
        return redirect(url_for("login"))

    info = resp.json()
    email = info.get("email")
    google_id = info.get("id")
    full_name = info.get("name")

    user = User.query.filter(
        (User.email == email) | (User.google_id == google_id)
    ).first()

    if not user:
        user = User(
            full_name=full_name,
            email=email,
            google_id=google_id,
            password=None
        )
        db.session.add(user)
        db.session.commit()

    login_user(user)
    flash(f"Welcome {user.full_name}", "success")
    return redirect(url_for("page"))



@app.route('/', methods=['GET', 'POST'])
def index():
    form = Signup()
    return render_template("index.html", form=form)


@app.route('/page')
def page():
    chats = Chat_table.query.filter_by(user_id=current_user.id).order_by(Chat_table.created_at).all()
    return render_template("admin/intro_homepage.html", user=current_user, chats=chats)


@app.route('/signup', methods=['GET', 'POST'])
def sign_up():
    signup_form = Signup()
    login_form = LoginForm()

    if signup_form.validate_on_submit():
        hashed_password = generate_password_hash(
            signup_form.password.data,
            method='pbkdf2:sha256'
        )

        user = User(
            full_name=signup_form.full_name.data,
            email=signup_form.email.data,
            password=hashed_password,
        )

        db.session.add(user)
        db.session.commit()
        send_verification_email(user)
        flash("Verification email sent! Check your inbox.", "success")
        return redirect(url_for('login'))
    return render_template(
        'authentication.html',
        signup_form=signup_form,
        login_form=login_form,
        active_tab='signup'
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not User.email_verified:
        flash("Please verify your email before logging in.", "error")
        return redirect(url_for('login'))

    login_form = LoginForm()
    signup_form = Signup()

    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user and user.password:  # Email/password user only
            if user.check_password(login_form.password.data):
                login_user(user)
                return redirect(url_for('page'))

        flash("Invalid email or password.", "danger")

    return render_template(
        'authentication.html',
        login_form=login_form,
        signup_form=signup_form,
        active_tab='login'
    )


@app.route('/auth2')
def auth2():
    return render_template(
        'authentication.html',
        login_form=LoginForm(),
        signup_form=Signup()
    )


import smtplib
from datetime import datetime
import random
from flask import flash, redirect, render_template, session, url_for

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            # Generate 6-digit code
            code = f"{random.randint(100000, 999999)}"
            session['reset_code'] = code
            session['reset_email'] = user.email

            try:
                # Send HTML email
                msg = Message(
                    "GeoGBT Password Reset Verification Code",
                    recipients=[user.email]
                )
                msg.html = render_template(
                    "email_verification_code.html",
                    user_name=user.full_name,
                    code=code,
                    current_year=datetime.now().year
                )
                mail.send(msg)

                flash("A verification code has been sent to your email.", "info")
                return redirect(url_for('verify_code'))

            except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
                print("Password reset email failed:", e)

                flash(
                    "We couldn't send the verification email right now due to a network issue. "
                    "Please try again later.",
                    "warning"
                )

        else:
            flash("Email not found.", "danger")

    return render_template('forgot_password.html', form=form)


@app.route('/verify-code', methods=['GET','POST'])
def verify_code():
    form = VerifyCodeForm()
    if form.validate_on_submit():
        if 'reset_code' in session and form.code.data == session['reset_code']:
            flash("Code verified! You can reset your password.", "success")
            return redirect(url_for('reset_password_code'))
        else:
            flash("Invalid code. Try again.", "danger")
    return render_template('verify_code.html', form=form)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/reset-password-code', methods=['GET', 'POST'])
def reset_password_code():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        email = session.get('reset_email')
        if email:
            user = User.query.filter_by(email=email).first()
            user.password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            db.session.commit()

            session.pop('reset_code', None)
            session.pop('reset_email', None)

            flash("Password reset successfully!", "success")
            return redirect(url_for('login'))
        else:
            flash("Session expired. Try again.", "danger")
            return redirect(url_for('forgot_password'))
    return render_template('reset_password.html', form=form)



@csrf.exempt
@app.route('/geoai', methods=['POST'])
def geoai():
    if not current_user.is_authenticated:
        return jsonify({'answer': 'Session expired. Please log in again.'}), 401

    data = request.get_json(silent=True)
    if not data or 'question' not in data:
        return jsonify({'answer': 'Invalid request.'}), 400

    question = data['question'].strip()
    if not question:
        return jsonify({'answer': 'Ask a geology or geophysics question.'}), 400

    # --- Check daily limit ---
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    today_count = Chat_table.query.filter(
        Chat_table.user_id == current_user.id,
        Chat_table.created_at >= cutoff
    ).count()

    if today_count >= DAILY_LIMIT:
        return jsonify({
            'answer': f"Sorry! You have reached your daily limit of {DAILY_LIMIT} GeoAI questions. Please try again tomorrow and also note that your chat history"
                      f" will be cleared after 24 hours"
        }), 429

    try:
        # --- Build AI prompt for concise answers ---
        prompt = f"""
You are a geoscience expert AI.
Answer geology, geophysics, petrophysics, and geophysical survey questions only.
Keep your answer concise — no more than 3-5 sentences.
Provide clear and direct explanations without unnecessary elaboration.

Question:
{question}
"""

        # --- Call GenAI ---
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )

        answer = response.text.strip()

        # --- Save chat in DB ---
        chat = Chat_table(
            user_id=current_user.id,
            question=question,
            answer=answer
        )
        db.session.add(chat)
        db.session.commit()

        return jsonify({
            "answer": answer
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'answer': 'AI service error. Try again.'}), 500




@app.route('/chat/<int:chat_id>')
def get_chat(chat_id):
    chat = Chat_table.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return "Unauthorized", 403
    return jsonify({'question': chat.question, 'answer': chat.answer})


@app.route('/list-models')
def list_models():
    models = client.models.list()
    return jsonify([m.name for m in models])




@app.route('/logout')
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for('login'))



@app.route("/chats")
def get_chats():
    page = request.args.get("page", 1, type=int)
    per_page = 50

    pagination = Chats.query.filter_by(user_id=current_user.id) \
        .order_by(Chats.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    chats = pagination.items

    return jsonify({
        "chats": [
            {
                "id": chat.id,
                "question": chat.question,
                "answer": chat.answer,
                "created_at": chat.created_at.strftime("%Y-%m-%d %H:%M"),
                "can_delete": True
            }
            for chat in chats
        ],
        "total_pages": pagination.pages,
        "current_page": pagination.page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    })


@app.route("/delete-chat/<int:chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    chat = Chats.query.filter_by(id=chat_id, user_id=current_user.id).first()

    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    db.session.delete(chat)
    db.session.commit()
    return jsonify({"success": "Chat deleted successfully"})



@app.route("/delete-all-chats", methods=["DELETE"])
def delete_all_chats():
    Chats.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"success": "All chats deleted"})




@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'], max_age=3600)
    except SignatureExpired:
        flash("The verification link has expired. Please sign up again.", "error")
        return redirect(url_for('sign_up'))
    except BadSignature:
        flash("Invalid verification link.", "error")
        return redirect(url_for('sign_up'))

    user = User.query.filter_by(email=email).first_or_404()
    if user.email_verified:
        flash("Email already verified. Please Sign in.", "info")
    else:
        user.email_verified = True
        db.session.commit()
        flash("Email verified successfully! You can now log in.", "success")

    return redirect(url_for('page'))



@app.route("/sitemap.xml")
def sitemap():
    return Response(
        """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://geogbt.onrender.com/</loc>
  </url>
  <url>
    <loc>https://geogbt.onrender.com/</loc>
  </url>
</urlset>""",
        mimetype="application/xml"
    )


# END OF THE ROUTES

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')