from google.appengine.ext.db import to_dict
from google.appengine.api import mail

from piston.handler import BaseHandler, AnonymousBaseHandler
from piston.utils import rc

from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template.loader import get_template
from django.template import Context

from mvp.models import validate

from fbapi import facebook

from models import *
from forms import *

from fanmento import settings

def send_welcome_email(user):
    welcome_email = get_template('new_user_email.html')
    html_content = welcome_email.render(Context({
        'name': user.name and user.name or user.email,
        'static_img_path': settings.STATIC_IMG_PATH
    }))

    try:
        message = mail.EmailMessage(sender=settings.MAIL_SENDER,
                subject="Welcome to Fanmento!")

        message.to = user.email
        message.html = html_content

        message.send()
    except mail.InvalidSenderError:
        logging.error("Invalid sender")

class RegistrationHandler(AnonymousBaseHandler):
    allowed_methods = ('POST',)

    def validate_facebook(self, email, token):
        if settings.DEBUG:
            return True

        try:
            graph = facebook.GraphAPI(token)
            profile = graph.get_object("me")
        except:
            return None

        return profile['email'] == email

    @validate(CreateUserForm, 'POST')
    def create(self, request):
        response = None

        have_token = 'facebook_token' in request.REQUEST.keys()
        if have_token and not self.validate_facebook(request.form.cleaned_data['email'], request.form.cleaned_data['facebook_token']):
            return rc.FORBIDDEN
        
        name = None
        if request.form.cleaned_data['name']:
            name = request.form.cleaned_data['name']

        (user, send_email, error) = create_new_user(name,
                request.form.cleaned_data['email'].lower(),
                ('password' in request.form.cleaned_data.keys()) and request.form.cleaned_data['password'] or None,
                have_token and request.form.cleaned_data['facebook_token'] or None, )

        if error:
            response = rc.DUPLICATE_ENTRY
            response.write('\nEmail is already in use')
            return response

        if send_email:
            send_welcome_email(user)

        return user.export_to_dict()

class UserHandler(BaseHandler):
    allowed_methods = ('GET', 'POST', 'PUT',)
    anonymous = RegistrationHandler

    def read(self, request, user_id=None):
        if user_id == None:
            user_id = request.user.key().id()

        try:
            user = User.get_by_id(user_id)
            return user.export_to_dict()
        except:
            return rc.NOT_FOUND

    def update_profile_photo(self, request):
        return rc.NOT_HERE

    def update_password(self, request):
        return rc.NOT_HERE

    def update_email(self, request):
        return rc.NOT_HERE

    def update_username(self, request):
        return rc.NOT_HERE

    def update(self, request):
        if 'email' in request.REQUEST.keys():
            return self.update_email(request)
        elif 'password' in request.REQUEST.keys():
            return self.update_password(request)
        elif 'username' in request.REQUEST.keys():
            return self.update_username(request)

        return rc.NOT_HERE

class UserImageDetailHandler(BaseHandler):
    allowed_methods = ('DELETE',)

    def delete(self, request, image_id):
        image = FanImage.get_by_id(int(image_id))

        if not image:
            return rc.NOT_FOUND

        if image.user.key() != request.user.key():
            return rc.FORBIDDEN

        image.delete()

        return rc.DELETED

class UserImageHandler(BaseHandler):
    allowed_methods = ('GET', 'POST',)

    @validate(UserImageForm, 'POST')
    def create(self, request):
        if not 'image' in request.FILES.keys():
            return rc.BAD_REQUEST

        fimage = FanImage(user=request.user,
                background_url=request.form.cleaned_data['background_url'],
                twitter_message=request.form.cleaned_data['twitter_message'],
                facebook_message=request.form.cleaned_data['facebook_message'],
                email_message=request.form.cleaned_data['email_message'],
                client_name=request.form.cleaned_data['client_name'])
        fimage.upload_image(request.FILES['image'].read(), request.FILES['image'].name)
        fimage.put()

        resp = rc.CREATED
        resp.content = {
                'id': fimage.key().id(),
        }
        return resp

    def read(self, request):
        def paginated_response(collection):
            page = request.GET.get('page', 1)

            p = Paginator(collection, 20)

            try:
                results = p.page(page)
            except (EmptyPage, InvalidPage):
                results = p.page(p.num_pages)

            return {
                'resources': results.object_list,
                'num_pages': p.num_pages,
            }

        user_id = request.user.key().id()
        user = User.get_by_id(user_id)

        return paginated_response([i.to_dict() for i in user.images.order('-created')])

class ResetTokenHandler(BaseHandler):
    allowed_methods = ('GET',)

    def days_ago(self, days):
        return datetime.datetime.now() - datetime.timedelta(days=days)

    def read(self, request):
        q = PasswordResetToken.all()
        q.filter("expires <", self.days_ago(2))

        tokens = q.run(batch_size=1000)

        for t in tokens:
            t.delete()

        return rc.ALL_OK
