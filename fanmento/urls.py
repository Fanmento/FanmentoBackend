from django.conf.urls.defaults import patterns, include

urlpatterns = patterns(
    '',
    (r'^api/v1/user/', include('fanmento.users.urls')),
    (r'^api/v1/templates/', include('fanmento.fantemplate.urls')),
    (r'^admin', include('fanmento.admin.urls')),
    (
        r'^mu-7e31d595-0ab0489f-8b41e6f9-953ab3e6',
        'fanmento.fantemplate.views.blitz_io'
    ),
)
