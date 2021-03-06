from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    )

import logging
log = logging.getLogger(__name__)

from flask.ext.login import UserMixin

from passlib.hash import sha256_crypt

from .support import db
from wtforms import StringField, validators, PasswordField
from wtforms.fields.html5 import EmailField
from ..forms import Form

class User(db.Model, UserMixin):
    """
    A user who can login and work with Dexter.
    """
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True)
    email       = Column(String(50), index=True, nullable=False, unique=True)
    first_name  = Column(String(50), nullable=False)
    last_name   = Column(String(50), nullable=False)
    admin       = Column(Boolean, default=False)
    disabled    = Column(Boolean, default=False)
    encrypted_password = Column(String(100))

    created_at   = Column(DateTime(timezone=True), index=True, unique=False, nullable=False, server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.current_timestamp())

    def get_password(self):
        return None

    def set_password(self, password):
        if password:
            self.encrypted_password = sha256_crypt.encrypt(password)


    def short_name(self):
        s = ""
        if self.first_name:
            s += self.first_name
        
        if self.last_name:
            if s:
                s += " " + self.last_name[0] + "."
            else:
                s = self.last_name

        if not s:
            s = self.email

        return s

    def full_name(self):
        s = '%s %s' % (self.first_name or '', self.last_name or '')
        s = s.strip()

        if not s:
            s = self.email

        return s


    password = property(get_password, set_password)

    def __repr__(self):
        return "<User email=%s>" % (self.email,)

    @classmethod
    def get_and_authenticate(cls, email, password):
        user = cls.query.filter(User.email == email).first()
        if user and not user.disabled and sha256_crypt.verify(password, user.encrypted_password):
            return user

        return None


class LoginForm(Form):
    email       = EmailField('Email', [validators.Required()])
    password    = PasswordField('Password', [validators.Required()])
