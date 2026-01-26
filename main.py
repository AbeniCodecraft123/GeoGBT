import math
import random
import os
from openai import OpenAI
from dotenv import load_dotenv
import traceback
load_dotenv()
from flask_dance.contrib.google import make_google_blueprint, google
from flask import Flask, render_template, redirect, flash, url_for, session, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, UserMixin
from wtforms import StringField, PasswordField, SubmitField, EmailField, DateField, TextAreaField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['secret_key'] = os.getenv('APP_SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('CRSF_KEY')
from flask_mail import Mail, Message
from flask_migrate import Migrate



app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'abenicodecraft001@gmail.com'
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = 'aishat.jamb20@gmail.com'



client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
mail = Mail(app)

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
migrate = Migrate(app, db)
#CREATING TABLE
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255))  # Only for email/password users
    full_name = db.Column(db.String(100))
    chats = db.relationship('Chat_table', backref='user', lazy=True)

    def __init__(self, full_name, email, password):
        self.full_name = full_name
        self.email = email
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.full_name, self.email, self.password

    def set_password(self, password):
        self.password = generate_password_hash(password)

    # Verify password during login
    def check_password(self, password):
        return check_password_hash(self.password, password)

    def obj_to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'password': self.password,
            'created_at': self.created_at,
            'chats': self.chats
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
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

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


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm', 'ogg'}


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
from werkzeug.security import generate_password_hash

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
        flash('You can now proceed to login', 'success')
        return redirect(url_for('login'))

    return render_template(
        'authentication.html',
        signup_form=signup_form,
        login_form=login_form,
        active_tab='signup'
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    signup_form = Signup()

    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user and user.password:  # make sure it’s not a Google-only user
            if check_password_hash(user.password, login_form.password.data):
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

            # Send email
            msg = Message("Password Reset Code", recipients=[user.email])
            msg.body = f"Your password reset code is: {code}"
            mail.send(msg)

            flash("A verification code has been sent to your email.", "info")
            return redirect(url_for('verify_code'))
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

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a geoscience expert AI. Only answer geology, geophysics, petrophysics, and geophysical survey questions."},
                {"role": "user", "content": question}
            ],
            temperature=0.2,
            max_tokens=400
        )

        answer = response.choices[0].message.content.strip()

        # Save chat ONLY if user is logged in
        chat = Chat_table(user_id=current_user.id, question=question, answer=answer)
        db.session.add(chat)
        db.session.commit()

        return jsonify({'answer': answer})

    except Exception as e:
        import traceback
        traceback.print_exc()  # <-- shows real error in console
        return jsonify({'answer': str(e)}), 500



@app.route('/chat/<int:chat_id>')
def get_chat(chat_id):
    chat = Chat_table.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return "Unauthorized", 403
    return jsonify({'question': chat.question, 'answer': chat.answer})


@app.route('/test-openai')
def test_openai():
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Define porosity in petrophysics"}
        ],
        max_tokens=100
    )
    return response.choices[0].message.content



@app.route('/logout')
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for('index'))



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



with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')