from django.http import HttpResponse

from models import *


def image_response(model):
    if model:
        return model.get_blob_response()

    response = HttpResponse()
    response.status_code = 404

    return response


def background_image(request, bg_id):
    return image_response(Background.get_by_id(int(bg_id)))


def template_image(request, template_id):
    return image_response(Template.get_by_id(int(template_id)))


def ad_image(request, ad_id):
    return image_response(Advertisement.get_by_id(int(ad_id)))


def blitz_io(request):

    """ Used to validate ownership of the site for Blitz.io testing"""

    return HttpResponse('42')
