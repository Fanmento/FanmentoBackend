from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    (r'/login$', 'fanmento.admin.views.admin_login'),
    (r'/logout$', 'fanmento.admin.views.admin_logout'),
    (r'/users/reset/request$', 'fanmento.admin.views.request_password_reset'),
    (r'/users/image/delete$', 'fanmento.admin.views.delete_image'),
    (r'/users/reset$', 'fanmento.admin.views.reset_password'),
    (r'/users/delete$', 'fanmento.admin.views.delete_user'),
    (r'/users/new$', 'fanmento.admin.views.create_user'),
    (r'/users/(?P<user_id>[^/]+)$', 'fanmento.admin.views.user_detail'),
    (r'/users$', 'fanmento.admin.views.users'),
    (r'/venues/delete$', 'fanmento.admin.views.delete_venue'),
    (r'/venues/new$', 'fanmento.admin.views.create_venue'),
    (r'/venues/(?P<venue_id>[^/]+)$', 'fanmento.admin.views.venue_detail'),
    (r'/venues$', 'fanmento.admin.views.venues'),
    (r'/advertisements/delete$', 'fanmento.admin.views.delete_advertisement'),
    (r'/advertisements/new$', 'fanmento.admin.views.create_advertisement'),
    (r'/advertisements/(?P<ad_id>[^/]+)$', 'fanmento.admin.views.advertisement_detail'),
    (r'/advertisements$', 'fanmento.admin.views.advertisements'),
    (r'/templates/delete$', 'fanmento.admin.views.delete_template'),
    (r'/templates/new$', 'fanmento.admin.views.create_template'),
    (r'/templates/(?P<template_id>[^/]+)$', 'fanmento.admin.views.template_detail'),
    (r'/templates$', 'fanmento.admin.views.templates'),
    (r'/backgrounds/delete$', 'fanmento.admin.views.delete_background'),
    (r'/backgrounds/new$', 'fanmento.admin.views.create_background'),
    (r'/backgrounds/(?P<bg_id>[^/]+)$', 'fanmento.admin.views.background_detail'),
    (r'/backgrounds$', 'fanmento.admin.views.backgrounds'),
    (r'/$', 'fanmento.admin.views.index'),
)
