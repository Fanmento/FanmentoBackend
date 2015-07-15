from django.shortcuts import render_to_response, redirect
from django.contrib.auth import authenticate, login
from django.http import HttpResponseNotFound, HttpResponseServerError, HttpResponse
from django.core.context_processors import csrf
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse

from google.appengine.ext import db

from passlib.hash import sha256_crypt

import logging
import datetime

from fanmento.users.models import *
from fanmento.users.forms import *

from fanmento.fantemplate.models import *
from fanmento.fantemplate.forms import *

from gae_utilities.paginator import GAEPaginator

def login_required(function):
    def unauthorized():
        return redirect('/admin/login')

    def error(e):
        response = HttpResponseServerError()
        response.write(e)
        return response

    def wrapped_f(*args, **kwargs):
        try:
            if args[0].session and args[0].session.has_key('user'):
                args[0].user = args[0].session['user']
                return function(*args, **kwargs)
            else:
                logging.error("Unauthorized")
                return unauthorized()
        except Exception as e:
            logging.error("Exception -> %s" % e)
            return error("Exception -> %s" % e.message)
        
    return wrapped_f

def admin_login(request):
    context = {
        'title': 'Login',
    }
    context.update(csrf(request))

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None and user.admin:
            request.session.regenerate_id()
            
            request.session['user'] = user

            return redirect(reverse('fanmento.admin.views.users'))
        else:
            # Return an 'invalid login' error message.
            context['error'] = True
            return render_to_response('login.html', context)

    return render_to_response('login.html', context)

def admin_logout(request):
    request.session.clear()

    return redirect(reverse('fanmento.admin.views.admin_login'))

@login_required
def index(request):
    return render_to_response('index.html', {
        'title': 'Fanmento Administration',
        'name': request.user.email,
        'active': 'index',
    })

@login_required
def users(request):
    order = request.GET.get('sort', 'name')
    users = db.Query(User).order(order)

    page = request.GET.get('page', 1)

    p = GAEPaginator(users, 20)

    try:
        results = p.page(page)
    except (EmptyPage, InvalidPage):
        results = p.page(p.num_pages)

    context = {
        'title': 'Fanmento Administration - Users',
        'name': request.user.email,
        'page': results,
        'sort': order,
        'active': 'users',
    }
    context.update(csrf(request))

    return render_to_response('users_list.html', context)

@login_required
def user_detail(request, user_id):
    u = User.get_by_id(int(user_id))
    if request.method == 'POST':
        f = RegistrationResourceForm(request.POST)
        if f.is_valid():
            u.email = f.cleaned_data['email']

            if f.cleaned_data['name']:
                u.name = f.cleaned_data['name']

            if f.cleaned_data['password']:
                password_hash = sha256_crypt.encrypt(f.cleaned_data['password'])
                u.password = password_hash

            u.admin = f.cleaned_data['admin']
            u.put()

            return redirect(users)
    else:
        f = RegistrationResourceForm(initial={
            'name': u.name,
            'email': u.email,
            'admin': u.admin,
        })

    context = {
        'title': 'Fanmento Administration - Update User',
        'name': request.user.email,
        'form': f,
        'images': [i.to_dict() for i in u.images.order('-created')],
        'update': True,
        'user_id': user_id,
        'active': 'users',
    }
    context.update(csrf(request))
    return render_to_response('users_new.html', context)

@login_required
def delete_image(request):
    if request.method == 'POST':
        f = ImageDeleteForm(request.POST)
        if f.is_valid():
            i = FanImage.get_by_id(int(f.cleaned_data['image_id']))
            i.delete()

    return redirect(user_detail, user_id=int(f.cleaned_data['user_id']))

@login_required
def delete_user(request):
    if request.method == 'POST':
        for rid in request.REQUEST.getlist('resource-ids[]'):
            u = User.get_by_id(int(rid))
            u.delete()

    return redirect(users)

@login_required
def create_user(request):
    if request.method == 'POST':
        f = RegistrationResourceForm(request.POST)
        if f.is_valid():
            (user, send_email, error) = create_new_user(
                    f.cleaned_data['name'],
                    f.cleaned_data['email'],
                    f.cleaned_data['password'], None)

            user.admin = f.cleaned_data['admin']
            user.put()

            if error:
                logging.info("Error when creating user!")

            return redirect(users)
    else:
        f = RegistrationResourceForm()

    context = {
        'title': 'Fanmento Administration - Create User',
        'name': request.user.email,
        'form': f,
        'active': 'users',
    }
    context.update(csrf(request))

    return render_to_response('users_new.html', context)

@login_required
def venues(request):
    order = request.GET.get('sort', 'name')

    venues = db.Query(Venue).order(order)

    page = request.GET.get('page', 1)

    p = GAEPaginator(venues, 20)

    try:
        results = p.page(page)
    except (EmptyPage, InvalidPage):
        results = p.page(p.num_pages)

    context = {
        'title': 'Fanmento Administration - Venues',
        'name': request.user.email,
        'page': results,
        'sort': order,
        'active': 'venues',
    }
    context.update(csrf(request))
    return render_to_response('venues_list.html', context)

@login_required
def venue_detail(request, venue_id):
    def split_address(address):
        result = {}
        fields = address.split(',')

        result['street'] = fields[0].strip()
        result['city'] = fields[1].strip()

        state_zip = fields[2].split(' ')
        result['state'] = state_zip[1].strip()
        result['zip'] = state_zip[2].strip()

        return result

    v = Venue.get_by_id(int(venue_id))
    if request.method == 'POST':
        f = VenueForm(request.POST)
        if f.is_valid():
            a = '%s, %s, %s %s' % (f.cleaned_data['street'], 
                    f.cleaned_data['city'], 
                    str(f.cleaned_data['state']), 
                    str(f.cleaned_data['zip']))
            v.name = f.cleaned_data['name']
            v.address = str(a)
            v.location = db.GeoPt(f.cleaned_data['latitude'],
                        f.cleaned_data['longitude'])

            (start_date, end_date) = f.cleaned_data['valid_dates'].split(" - ")
            v.start_date = datetime.datetime.strptime(start_date, "%m/%d/%Y").date()
            v.end_date = datetime.datetime.strptime(end_date, "%m/%d/%Y").date()

            v.update_location()
            v.put()

            return redirect(venues)
    else:
        address = split_address(v.address)
        f = VenueForm(initial={
            'name': v.name,
            'street': address['street'],
            'city': address['city'],
            'state': address['state'],
            'zip': address['zip'],
            'latitude': v.location.lat,
            'longitude': v.location.lon,
            'valid_dates': v.date_string()
        })

    context = {
        'title': 'Fanmento Administration - Update Venue',
        'name': request.user.email,
        'form': f,
        'update': True,
        'venue_id': venue_id,
        'active': 'venues',
    }
    context.update(csrf(request))
    return render_to_response('venues_new.html', context)

@login_required
def delete_venue(request):
    if request.method == 'POST':
        for rid in request.REQUEST.getlist('resource-ids[]'):
            v = Venue.get_by_id(int(rid))
            v.delete()

    return redirect(venues)

@login_required
def create_venue(request):
    if request.method == 'POST':
        f = VenueForm(request.POST)
        if f.is_valid():
            logging.info("Form valid")
            (start_date, end_date) = f.cleaned_data['valid_dates'].split(" - ")

            venue = Venue(name=f.cleaned_data['name'],
                    address=db.PostalAddress('%s, %s, %s %s' %
                        (f.cleaned_data['street'],
                            f.cleaned_data['city'],
                            f.cleaned_data['state'],
                            f.cleaned_data['zip'])),
                    location=db.GeoPt(f.cleaned_data['latitude'],
                        f.cleaned_data['longitude']),
                    start_date=datetime.datetime.strptime(start_date, "%m/%d/%Y").date(),
                    end_date=datetime.datetime.strptime(end_date, "%m/%d/%Y").date()
            )
            venue.update_location()
            venue.put()

            return redirect(venues)
    else:
        f = VenueForm()

    context = {
        'title': 'Fanmento Administration - Create Venue',
        'name': request.user.email,
        'form': f,
        'active': 'venues',
    }
    context.update(csrf(request))

    return render_to_response('venues_new.html', context)

@login_required
def advertisements(request):
    order = request.GET.get('sort', 'name')

    ads = db.Query(Advertisement).order(order)

    page = request.GET.get('page', 1)

    p = GAEPaginator(ads, 20)

    try:
        results = p.page(page)
    except (EmptyPage, InvalidPage):
        results = p.page(p.num_pages)

    context = {
        'title': 'Fanmento Administration - Advertisements',
        'name': request.user.email,
        'page': results,
        'sort': order,
        'active': 'advertisements',
    }
    context.update(csrf(request))
    return render_to_response('ads_list.html', context)

@login_required
def advertisement_detail(request, ad_id):
    a = Advertisement.get_by_id(int(ad_id))
    if request.method == 'POST':
        f = AdvertisementForm(request.POST)
        if f.is_valid():
            a.name = f.cleaned_data['name']
            a.description = f.cleaned_data['description']
            a.company = f.cleaned_data['company']
            a.link = f.cleaned_data['link']

            if 'image' in request.FILES:
                a.upload_image(request.FILES['image'].read(), request.FILES['image'].name)

            a.put()

            return redirect(advertisements)
    else:
        f = AdvertisementForm(initial={
            'name': a.name,
            'description': a.description,
            'company': a.company,
            'link': a.link,
        })

    context = {
        'title': 'Fanmento Administration - Update Advertisement',
        'name': request.user.email,
        'form': f,
        'update': True,
        'ad_id': ad_id,
        'active': 'advertisements',
    }
    context.update(csrf(request))
    return render_to_response('ads_new.html', context)

@login_required
def delete_advertisement(request):
    if request.method == 'POST':
        for rid in request.REQUEST.getlist('resource-ids[]'):
            a = Advertisement.get_by_id(int(rid))
            a.delete()

    return redirect(advertisements)

@login_required
def create_advertisement(request):
    if request.method == 'POST':
        f = AdvertisementForm(request.POST, request.FILES)
        if f.is_valid():
            ad = Advertisement(name=f.cleaned_data['name'],
                    description=f.cleaned_data['description'],
                    company=f.cleaned_data['company'],
                    link=f.cleaned_data['link'],
                    clicks=0,
                    impressions=0)

            if 'image' in request.FILES:
                ad.upload_image(request.FILES['image'].read(), request.FILES['image'].name)

            ad.put()

            return redirect(advertisements)
    else:
        f = AdvertisementForm()

    context = {
        'title': 'Fanmento Administration - Create Ad',
        'name': request.user.email,
        'form': f,
        'active': 'advertisements',
    }
    context.update(csrf(request))

    return render_to_response('ads_new.html', context)

@login_required
def templates(request):
    order = request.GET.get('sort', 'name')
    page = request.GET.get('page', 1)

    if 'venue' in order: 
        templates = db.Query(Template)
        templates = sorted([t for t in templates], key=lambda t: t.venue and t.venue.name or 'ZZZZZZZ', reverse='-' in order)
        p = Paginator(templates, 20)
    else:
        templates = db.Query(Template).order(order)
        p = GAEPaginator(templates, 20)

    try:
        results = p.page(page)
    except (EmptyPage, InvalidPage):
        results = p.page(p.num_pages)

    context = {
        'title': 'Fanmento Administration - Templates',
        'name': request.user.email,
        'page': results,
        'sort': order,
        'active': 'templates',
    }
    context.update(csrf(request))
    return render_to_response('templates_list.html', context)

@login_required
def template_detail(request, template_id):
    t = Template.get_by_id(int(template_id))

    def related_field(c):
        try:
            if c.__name__ == 'Venue':
                if not t.venue:
                    return None
                return t.venue.key().id()
            elif c.__name__ == 'Advertisement':
                return t.advertisement.key().id()
            elif c.__name__ == 'Background':
                return t.background.key().id()
        except: pass
        
        return None

    if request.method == 'POST':
        f = UpdateTemplateForm(request.POST)

        if f.is_valid():
            ad = Advertisement.get_by_id(int(f.cleaned_data['advertisement']))

            venue = None
            venue_id = f.cleaned_data['venue']
            if venue_id != 'None':
                venue = Venue.get_by_id(int(venue_id))

            background = Background.get_by_id(int(f.cleaned_data['background']))

            t.name = f.cleaned_data['name']
            t.category = f.cleaned_data['category']
            t.code = f.cleaned_data['code'].lower()
            t.product_id = f.cleaned_data['product_id']
            t.description = f.cleaned_data['description']
            t.effect = f.cleaned_data['effect']
            t.twitter_message = f.cleaned_data['twitter_message']
            t.facebook_message = f.cleaned_data['facebook_message']
            t.email_message = f.cleaned_data['email_message']
            t.client_name = f.cleaned_data['client_name']
            t.advertisement = ad
            t.venue = venue
            t.background = background

            if 'image' in request.FILES:
                t.upload_image(request.FILES['image'].read(), request.FILES['image'].name)

            t.put()

            return redirect(templates)
    else:
        f = UpdateTemplateForm(initial={
            'name': t.name,
            #'image':t.image,
            'category': t.category,
            'code': t.code,
            'product_id': t.product_id,
            'description': t.description,
            'effect': t.effect,
            'twitter_message': t.twitter_message,
            'facebook_message': t.facebook_message,
            'email_message': t.email_message,
            'client_name': t.client_name,
            'advertisement': related_field(Advertisement),
            'venue': related_field(Venue),
            'background': related_field(Background)
            })

    context = {
        'title': 'Fanmento Administration - Update Template',
        'name': request.user.email,
        'form': f,
        'update': True,
        'template_id': template_id,
        'active': 'templates',
    }
    context.update(csrf(request))

    return render_to_response('templates_new.html', context)

@login_required
def delete_template(request):
    if request.method == 'POST':
        for rid in request.REQUEST.getlist('resource-ids[]'):
            t = Template.get_by_id(int(rid))
            t.delete()

    return redirect(templates)

@login_required
def create_template(request):
    if request.method == 'POST':
        f = TemplateForm(request.POST, request.FILES)
        if f.is_valid():
            ad = Advertisement.get_by_id(int(f.cleaned_data['advertisement']))

            venue = None
            venue_id = f.cleaned_data['venue']
            if venue_id != 'None':
                venue = Venue.get_by_id(int(venue_id))

            background = Background.get_by_id(int(f.cleaned_data['background']))

            template = Template(name=f.cleaned_data['name'],
                    category=f.cleaned_data['category'].lower(),
                    code=f.cleaned_data['code'],
                    product_id=f.cleaned_data['product_id'],
                    description=f.cleaned_data['description'],
                    effect=f.cleaned_data['effect'],
                    twitter_message=f.cleaned_data['twitter_message'],
                    facebook_message=f.cleaned_data['facebook_message'],
                    email_message=f.cleaned_data['email_message'],
                    client_name=f.cleaned_data['client_name'],
                    advertisement=ad,
                    venue=venue,
                    background=background)

            if 'image' in request.FILES:
                template.upload_image(request.FILES['image'].read(), request.FILES['image'].name)

            template.put()

            return redirect(templates)
    else:
        f = TemplateForm()

    context = {
        'title': 'Fanmento Administration - Create Template',
        'name': request.user.email,
        'form': f,
        'active': 'templates',
    }
    context.update(csrf(request))

    return render_to_response('templates_new.html', context)

@login_required
def backgrounds(request):
    backgrounds = db.Query(Background)

    page = request.GET.get('page', 1)

    p = GAEPaginator(backgrounds, 20)

    try:
        results = p.page(page)
    except (EmptyPage, InvalidPage):
        results = p.page(p.num_pages)

    context = {
        'title': 'Fanmento Administration - Backgrounds',
        'name': request.user.email,
        'page': results,
        'active': 'backgrounds',
    }
    context.update(csrf(request))
    return render_to_response('background_list.html', context)

@login_required
def background_detail(request, bg_id):
    b = Background.get_by_id(int(bg_id))
    if request.method == 'POST':
        f = BackgroundForm(request.POST)
        if f.is_valid():
            b.name = f.cleaned_data['name']
            b.description = f.cleaned_data['description']

            if 'image' in request.FILES:
                b.upload_image(request.FILES['image'].read(), request.FILES['image'].name)

            b.put()
    
            return redirect(backgrounds)
    else:
        f = BackgroundForm(initial={
            'name': b.name,
            'description': b.description,
        })

    context = {
        'title': 'Fanmento Administration - Update Background',
        'name': request.user.email,
        'form': f,
        'update': True,
        'background_id': bg_id,
        'active': 'backgrounds',
    }
    context.update(csrf(request))
    return render_to_response('background_new.html', context)

@login_required
def delete_background(request):
    if request.method == 'POST':
        for rid in request.REQUEST.getlist('resource-ids[]'):
            b = Background.get_by_id(int(rid))
            b.delete()

    return redirect(backgrounds)

@login_required
def create_background(request):
    if request.method == 'POST':
        f = BackgroundForm(request.POST, request.FILES)
        if f.is_valid():
            bg = Background(name=f.cleaned_data['name'],
                    description=f.cleaned_data['description'])

            if 'image' in request.FILES:
                bg.upload_image(request.FILES['image'].read(), request.FILES['image'].name)

            bg.put()

            return redirect(backgrounds)
    else:
        f = BackgroundForm()

    context = {
        'title': 'Fanmento Administration - Create Background',
        'name': request.user.email,
        'form': f,
        'active': 'backgrounds',
    }
    context.update(csrf(request))

    return render_to_response('background_new.html', context)

def request_password_reset(request):
    error, email = None, None

    def build_response(f, error, done):
        context = {
            'title': 'Request Password Reset',
            'form': f,
            'email': email,
            'error': error,
        }
        context.update(csrf(request))

        return render_to_response('request_password_reset.html', context)

    if request.method == 'POST':
        f = RequestResetPasswordForm(request.POST)
        if f.is_valid():
            email = f.cleaned_data['email'].lower()
            q = User.all().filter('email =', email)
            u = q.get()

            if u:
                token = u.get_reset_token()
                t = PasswordResetToken(user=u,
                        token=token)
                t.put()
            
                u.send_reset_email(token)
        else:
            done = 'Please enter an email address'
    else:
        f = RequestResetPasswordForm()

    return build_response(f, error, email)

def reset_password(request):
    error = None

    def build_response(f, error):
        t = None
        try:
            logging.info(request.REQUEST.get('token'))
            t = request.REQUEST['token']
        except KeyError:
            error = 'Token not provided or invalid'

        context = {
            'title': 'Reset Password',
            'form': f,
            'token': t,
            'error': error,
        }
        context.update(csrf(request))

        return render_to_response('reset_password.html', context)

    if request.method == 'POST':
        f = ResetPasswordForm(request.POST)

        if f.is_valid():
            if f.cleaned_data['password'] != f.cleaned_data['confirm']:
                error = 'Passwords did not match'
                return build_response(f, error)

            q = PasswordResetToken.all().filter('token =', f.cleaned_data['token'])
            t = q.get()

            if not t:
                error = 'Invalid or expired token'
                return build_response(f, error)

            u = t.user
            u.set_password(f.cleaned_data['password'])
            u.remove_tokens()

            context = {
                'title': 'Login',
                'alert': 'Your password has been reset.',
            }
            context.update(csrf(request))

            return render_to_response('login.html', context)
    else:
        logging.info("Generating basic form")
        f = ResetPasswordForm()

    return build_response(f, error)

def welcome_email(request):
    context = {
        'name': 'Scott',
    }
    context.update(csrf(request))

    return render_to_response('new_user_email.html', context)
