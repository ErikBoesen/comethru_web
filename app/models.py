from app import app, db, bcrypt
import datetime
import jwt
import hashlib
import dateutil.parser
import random


followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id'))
)

hostships = db.Table('hostships',
    db.Column('host_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'))
)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    registered_on = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    followed = db.relationship(
            'User', secondary=followers,
            primaryjoin=(followers.c.follower_id == id),
            secondaryjoin=(followers.c.followed_id == id),
            backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    hosted = db.relationship(
            'Event', secondary=hostships,
            primaryjoin=(hostships.c.host_id == id),
            secondaryjoin=(hostships.c.event_id == id),
            backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))

    def __init__(self, name, email, password, school_id, confirmed=False):
        self.name = name
        self.email = email
        self.password = bcrypt.generate_password_hash(
            password, app.config.get('BCRYPT_LOG_ROUNDS')
        ).decode()
        self.school_id = school_id
        self.confirmed = confirmed
        self.registered_on = datetime.datetime.now()

    def encode_token(self, user_id):
        """
        Generates the Auth Token
        :return: string
        """
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=365, seconds=0),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            app.config.get('SECRET_KEY'),
            algorithm='HS256'
        ), payload['exp']

    def avatar(self):
        return hashlib.md5(self.email.encode('utf-8')).hexdigest()

    @staticmethod
    def decode_token(token):
        """
        Validates the auth token
        :param token:
        :return: integer|string
        """
        try:
            payload = jwt.decode(token, app.config.get('SECRET_KEY'))
            is_blacklisted_token = BlacklistedToken.check_blacklist(token)
            if is_blacklisted_token:
                return 'Token blacklisted. Please log in again.'
            else:
                return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'

    def json(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'verified': self.verified,
            'avatar': self.avatar(),
        }

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    @staticmethod
    def from_token(token):
        user_id = User.decode_token(token)
        user = User.query.get(user_id)
        return user

class BlacklistedToken(db.Model):
    __tablename__ = 'blacklisted_tokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(500), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token
        self.blacklisted_on = datetime.datetime.now()

    @staticmethod
    def check_blacklist(auth_token):
        # check whether auth token has been blacklisted
        res = BlacklistedToken.query.filter_by(token=str(auth_token)).first()
        return bool(res)


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.String(1024))

    location = db.Column(db.String(127), nullable=False)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)

    time = db.Column(db.DateTime, nullable=False)

    hosts = db.relationship(
        'User', secondary=hostships,
        primaryjoin=(hostships.c.event_id == id),
        secondaryjoin=(hostships.c.host_id == id),
        backref=db.backref('hostships', lazy='dynamic'), lazy='dynamic')

    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))

    def __init__(self, raw):
        self.time = dateutil.parser.parse(raw.pop('time', None))
        for field in raw:
            setattr(self, field, raw[field])
        self.registered_on = datetime.datetime.now()

    def add_host(self, user):
        self.hosts.add(user)

    def hosted_by(self, user):
        self.hosts.filter(self.hosts.c.host_id == user.id).count() > 0

    def json(self):
        raw = {key: getattr(self, key) for key in ('id', 'name', 'description',
                                                   'location', 'lat', 'lng',
                                                   'time')}
        raw.update({
            'people': random.randint(0, 50),
            'rating': random.randint(0, 100),
        })
        return raw


class School(db.Model):
    __tablename__ = 'schools'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True)
    nickname = db.Column(db.String(16), unique=True)
    color = db.Column(db.String(6), nullable=True)
    domain = db.Column(db.String(32), unique=True)

    students = db.relationship('User', backref='users', lazy='dynamic')
    events = db.relationship('Event', backref='events', lazy='dynamic')

    @staticmethod
    def get_by_email(email):
        domain = email.split('@')[-1]
        return School.query.filter_by(domain=domain).first()
