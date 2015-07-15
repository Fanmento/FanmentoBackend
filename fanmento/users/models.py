from passlib.hash import sha256_crypt

from google.appengine.api import mail
from google.appengine.ext import db, blobstore
from google.appengine.ext.db import to_dict

from django.core.urlresolvers import reverse

import logging
import datetime
import pytz

from fanmento import settings

from gae_utilities.models import BlobModel

def int_to_base36(i):
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    factor = 0
    # Find starting factor
    while True:
        factor += 1
        if i < 36 ** factor:
            factor -= 1
            break
    base36 = []
    # Construct base36 representation
    while factor >= 0:
        j = 36 ** factor
        base36.append(digits[i / j])
        i = i % j
        factor -= 1
    return ''.join(base36)

class User(db.Model):
    name     = db.StringProperty()
    password = db.StringProperty()
    email    = db.EmailProperty()
    admin    = db.BooleanProperty(default=False)

    def export_to_dict(self):
        return {
            'name': self.name,
            'email': self.email,
        }

    def set_password(self, password):
        password_hash = sha256_crypt.encrypt(password)
        self.password = password_hash

        self.put()

    def get_reset_token(self):
        timestamp = (datetime.datetime.now() - datetime.datetime(2001, 1, 1)).days
        ts_b36 = int_to_base36(timestamp)

        from django.utils.hashcompat import sha_constructor
        hash = sha_constructor(settings.SECRET_KEY + unicode(self.key().id()) +
                self.password +
                unicode(timestamp)).hexdigest()[::2]
        return "%s-%s" % (ts_b36, hash)

    def remove_tokens(self):
        for t in self.tokens:
            t.delete()

    def clean_up_facebook_tokens(self, keep_amount=10):
        all_facebook_tokens = list(self.facebook_tokens.order('-created'))
        tokens_to_remove = all_facebook_tokens[keep_amount:]
        for t in tokens_to_remove:
            t.delete()

    def send_reset_email(self, token):
        reset_url = '%s?token=%s' % (reverse('fanmento.admin.views.reset_password'), token)
        mail.send_mail(sender=settings.MAIL_SENDER,
                      to=self.email,
                      subject="Password reset request",
                      body="Please visit %s%s" % (settings.BASE_URL, reset_url))


class FacebookToken(db.Model):
    user    = db.ReferenceProperty(User, collection_name='facebook_tokens')
    token   = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)


class PasswordResetToken(db.Model):
    user    = db.ReferenceProperty(User, collection_name='tokens')
    token   = db.StringProperty()
    expires = db.DateTimeProperty(auto_now_add=True)

def create_new_user(name, email, password, facebook_token):
    send_email = False

    def put_user(phash):
        try:
            user = User(name=name, password=phash, email=email)
            user.put()
        except Exception as e:
            logging.error(e)

        return user

    q = User.all()
    q.filter("email =", email)

    user = q.get()
    if (user and password):
        return None, send_email, True

    password_hash = None
    if password:
        password_hash = sha256_crypt.encrypt(password)
        user = put_user(password_hash)
        send_email = True
    elif facebook_token:
        if facebook_token:
            token_hash = sha256_crypt.encrypt(facebook_token)

            if not user: 
                user = put_user(None)
                send_email = True

            token = FacebookToken(user=user, token=token_hash)
            token.put()

            if name:
                user.name = name
                user.put()

    return user, send_email, False

class FanImage(BlobModel):
    user             = db.ReferenceProperty(User, collection_name="images")
    created          = db.DateTimeProperty(auto_now_add=True)
    background_url   = db.StringProperty()
    twitter_message  = db.TextProperty()
    facebook_message = db.TextProperty()
    email_message    = db.TextProperty()
    client_name      = db.StringProperty()

    def to_dict(self):
        cst = pytz.timezone('US/Central')

        result = to_dict(self)
        result['id'] = self.key().id()
        result['timestamp'] = self.created.replace(tzinfo=pytz.utc).astimezone(cst)
        result['created'] = self.created.strftime("%Y-%m-%dT%H:%M:%S")
        return result
