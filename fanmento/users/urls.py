from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

from mvp.models import Resource
from piston.authentication import HttpBasicAuthentication
from api import *

authentication = {
    'authentication': HttpBasicAuthentication(realm='fanmento')
}

urlpatterns = patterns('',
    (r'reset/clear$', Resource(handler=ResetTokenHandler)),
    (r'image/(?P<image_id>[^/]+)/?$', Resource(handler=UserImageDetailHandler, **authentication)),
    (r'image/?$', Resource(handler=UserImageHandler, **authentication)),
    (r'(?P<user_id>[^/]+)$', Resource(handler=UserHandler, **authentication)),
    (r'$', Resource(handler=UserHandler, **authentication)),
)
