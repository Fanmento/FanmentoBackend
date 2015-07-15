from django import forms
from django.contrib.localflavor.us.forms import USStateField, USZipCodeField
from django.utils.safestring import mark_safe
from django.forms import widgets

from google.appengine.ext import db

from bootstrap.forms import BootstrapForm, Fieldset

import logging

from models import *

class CalendarWidget(widgets.TextInput):
    def render(self, name, value, attrs=None):
        return mark_safe(u'''
                <div class="input-prepend">
                    <span class="add-on"><i class="icon-calendar"></i></span>%s
                </div>
                ''' % (super(CalendarWidget, self).render(name, value, attrs)))

class VenueForm(BootstrapForm):
    class Meta:
        layout = (
            Fieldset("Update a venue", 
                "name", 
                "street", 
                "city", 
                "state",
                "zip",
                "latitude",
                "longitude",
                "valid_dates",
            ),
        )

    name        = forms.CharField(max_length=75)
    street      = forms.CharField(max_length=75)
    city        = forms.CharField(max_length=25)
    state       = USStateField()
    zip         = USZipCodeField()
    latitude    = forms.DecimalField()
    longitude   = forms.DecimalField()
    valid_dates = forms.CharField(widget=CalendarWidget)

class AdvertisementForm(BootstrapForm):
    error_css_class = 'error'
    required_css_class = 'required'

    name        = forms.CharField(max_length=75)
    image       = forms.FileField(required=False)
    description = forms.CharField(widget=forms.Textarea)
    company     = forms.CharField(max_length=75)
    link        = forms.CharField(max_length=75)

class PriceWidget(widgets.TextInput):
    def render(self, name, value, attrs=None):
        return mark_safe(u'''<div class="input-prepend input-append"><span class="add-on">$</span>%s</div>''' % (super(PriceWidget, self).render(name, value, attrs)))

class TemplateForm(BootstrapForm):
    error_css_class = 'error'
    required_css_class = 'required'

    def __init__(self, *args, **kwargs):
        super(TemplateForm, self).__init__(*args, **kwargs)
        
        q = db.Query(Advertisement, projection=("name",))
        ads = q.run(batch_size=1000)

        self.fields['advertisement'] = forms.ChoiceField(choices=[(a.key().id(), a.name) for a in ads])

        q = db.Query(Venue, projection=("name",))
        venues = q.run(batch_size=1000)

        venue_choices = [(v.key().id(), v.name) for v in venues]
        venue_choices.insert(0, ('None', None))
        self.fields['venue'] = forms.ChoiceField(choices=venue_choices)

        q = db.Query(Background, projection=("name",))
        backgrounds = q.run(batch_size=1000)

        self.fields['background'] = forms.ChoiceField(choices=[(b.key().id(), b.name) for b in backgrounds])

    CATEGORIES = (
        ('sports', 'Sports'),
        ('entertainment', 'Entertainment'),
        ('music', 'Music'),
        ('lifestyle', 'Lifestyle'),
        ('miscellaneous', 'Miscellaneous'),
    )

    name             = forms.CharField(max_length=75)
    image            = forms.FileField(required=True)
    code             = forms.CharField(max_length=5)
    product_id       = forms.CharField(max_length=50, label="IAP Product ID", required=False)
    category         = forms.ChoiceField(choices=CATEGORIES)
    description      = forms.CharField(widget=forms.Textarea)
    effect           = forms.ChoiceField(choices=Template.EFFECTS)
    twitter_message  = forms.CharField(widget=forms.Textarea, required=False)
    facebook_message = forms.CharField(widget=forms.Textarea, required=False)
    email_message    = forms.CharField(widget=forms.Textarea, required=False)
    client_name      = forms.CharField(max_length=75, required=False)

class UpdateTemplateForm(TemplateForm):
    image            = forms.FileField(required=False)

class TemplateQueryForm(forms.Form):
    latitude  = forms.DecimalField(required=False)
    longitude = forms.DecimalField(required=False)
    category  = forms.CharField(required=False)

class BackgroundForm(BootstrapForm):
    error_css_class = 'error'
    required_css_class = 'required'

    name        = forms.CharField(max_length=75)
    image       = forms.FileField(required=False)
    description = forms.CharField(widget=forms.Textarea)
