from flask import Blueprint, request, make_response, jsonify, url_for, render_template, redirect
from flask.views import MethodView
# For confirmation
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message

from app import app, db, mail, bcrypt
from app.models import User, School, BlacklistedToken
from app.util import succ, fail


auth = Blueprint('auth', __name__)

@auth.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        return render_template('confirm.html', message='Invalid or expired link.'), 401
        # TODO: what are they supposed to do then?
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        return render_template('confirm.html', message='Email already confirmed! Please log in.'), 200
    else:
        user.confirmed = True
        db.session.commit()
        return redirect(app.config['WEB_DOMAIN'] + '/confirmed'), 200


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    mail.send(msg)


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=app.config['CONFIRMATION_TOKEN_EXPIRATION'],
        )
        return email
    except:
        return False

@auth.route('/register', methods=['POST'])
def register():
    # get the post data
    payload = request.get_json()
    # check if user already exists
    user = User.query.filter_by(email=payload.get('email')).first()
    if not user:
        try:
            email = payload['email'].lower()
            with open('resources/email_blacklist.txt') as f:
                # TODO: should we just keep this in memory continuously rather than reading it every time?
                email_blacklist = f.read().split('\n')
                if email in email_blacklist:
                    return fail('Sorry, a student email address is required to register.', 401)
            school = School.from_email(email)
            if school is None:
                # TODO: use non-Yale-specific message.
                return fail('You must use a valid @yale.edu email address.', 401)

            user = User(
                name=payload['name'],
                email=email,
                password=payload['password'],
                confirmed=False,
                school_id=school.id,
            )
            # Insert the user
            db.session.add(user)
            db.session.commit()

            # Build and send confirmation email
            confirmation_token = generate_confirmation_token(user.email)
            confirm_url = url_for('auth.confirm_email', token=confirmation_token, _external=True)
            html = render_template('confirm_email.html', name=user.name.split()[0], confirm_url=confirm_url)
            subject = '🌙 Verify your email for Comethru!'
            send_email(user.email, subject, html)

            return succ('Check your email to confirm your address, then log in!', 201)
        except Exception as e:
            # TODO: eventually we should just return the error to the client
            raise e
            return fail('Some error occurred. Please try again. Contact the developers if this continues to happen.', 500)
    else:
        return fail('User already exists. Please log in.', 202)



@auth.route('/login', methods=['POST'])
def login():
    # get the post data
    payload = request.get_json()
    try:
        # fetch the user data
        user = User.query.filter_by(
            email=payload.get('email')
        ).first()
        if user and bcrypt.check_password_hash(user.password, payload.get('password')):
            if not user.confirmed:
                return fail('Please check your email to confirm your account before logging in!', 401)
            token, expires_in = user.generate_token()
            if token:
                response_data = {
                    'status': 'success',
                    'message': 'Successfully logged in.',
                    'token': token,
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        # do we need this?
                        'email': user.email,
                        'token': token,
                        'expires_in': expires_in,
                    }
                }
                return jsonify(response_data), 200
        else:
            return fail('Sorry, we couldn\'t recognize that email or password.', 404)
    except Exception as e:
        print(e)
        return fail('There was an unexpected error. Please try again! :)', 500)


@auth.route('/logout', methods=['POST'])
def logout():
    pass
    """
    # get auth token
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(' ')[1]
    else:
        token = ''
    if token:
        resp = User.decode_token(token)
        if not isinstance(resp, str):
            # mark the token as blacklisted
            blacklisted_token = BlacklistedToken(token=token)
            try:
                # insert the token
                db.session.add(blacklisted_token)
                db.session.commit()
                return succ('Successfully logged out.')
            except Exception as e:
                return fail(e), 200
        else:
            return fail(resp), 401
    else:
        return fail('Provide a valid auth token.', 403)
    """
