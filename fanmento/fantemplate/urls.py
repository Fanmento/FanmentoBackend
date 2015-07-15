from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

from mvp.models import Resource
from piston.authentication import HttpBasicAuthentication
from api import *

authentication = {
    'authentication': HttpBasicAuthentication(realm='fanmento')
}

urlpatterns = patterns('',
    (r'venue$', Resource(handler=VenueHandler, **authentication)),
    (r'ad/(?P<ad_id>[^/]+)/image$', 'fanmento.fantemplate.views.ad_image'),
    (r'ad/(?P<template_id>[^/]+)/?$', Resource(handler=AdvertisementHandler, **authentication)),
    (r'category$', Resource(handler=CategoryHandler, **authentication)),
    (r'background/(?P<bg_id>[^/]+)/image', 'fanmento.fantemplate.views.background_image'),
    (r'template/(?P<template_id>[^/]+)/image', 'fanmento.fantemplate.views.template_image'),
    (r'template/(?P<code>[^/]+)', Resource(handler=TemplateByCodeHandler, **authentication)),
    (r'template', Resource(handler=TemplateByQueryHandler, **authentication)),
)
