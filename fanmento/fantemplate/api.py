from google.appengine.ext import db
from google.appengine.api import memcache

from django.core.paginator import Paginator, InvalidPage, EmptyPage

from piston.handler import BaseHandler
from piston.utils import rc

from geo import geotypes

import logging
import datetime

from models import *
from forms import *

def prefetch_refprops(entities, *props):
    fields = [(entity, prop) for entity in entities for prop in props]
    ref_keys = [prop.get_value_for_datastore(x) for x, prop in fields]
    ref_entities = dict((x.key(), x) for x in db.get(set(ref_keys)))

    for (entity, prop), ref_key in zip(fields, ref_keys):
        prop.__set__(entity, ref_entities[ref_key])

    return entities

def make_cache_key(request):
    path = request.path
    query_string = request.META.get('QUERY_STRING','')
    return '{}?{}'.format(path, query_string)

class VenueHandler(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request):
        q = Venue.all()
        venues = q.run(batch_size=1000)

        return [v.to_dict() for v in venues]

class AdvertisementHandler(BaseHandler):
    allowed_methods = ('POST', 'PUT',)

    def create(self, request, template_id):
        t = Template.get_by_id(int(template_id))

        logging.debug("Template ID: %s" % template_id)
        if not t:
            return rc.NOT_FOUND

        a = Advertisement.get_by_id(t.advertisement.key().id())

        logging.debug("Ad ID: %d" % t.advertisement.key().id())
        if not a:
            return rc.NOT_FOUND

        a.clicks = a.clicks + 1
        a.put()

        return rc.ALL_OK

    def update(self, request, template_id):
        t = Template.get_by_id(int(template_id))

        logging.debug("Template ID: %s" % template_id)
        if not t:
            return rc.NOT_FOUND

        a = Advertisement.get_by_id(t.advertisement.key().id())

        logging.debug("Ad ID: %d" % t.advertisement.key().id())
        if not a:
            return rc.NOT_FOUND

        a.impressions = a.impressions + 1
        a.put()

        return rc.ALL_OK

class TemplateByCodeHandler(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request, code):
        q = Template.all().filter('code =', code.lower())
        q.order('name')
        templates = q.run(batch_size=1000)

        return [t.to_dict() for t in templates]

class TemplateByQueryHandler(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request):
        def paginated_response(collection):
            page = request.GET.get('page', 1)

            p = Paginator(collection, 10)

            try:
                results = p.page(page)
            except (EmptyPage, InvalidPage):
                results = p.page(p.num_pages)

            return {
                'resources': results.object_list,
                'num_pages': p.num_pages,
            }

        templates = None

        cache_key = make_cache_key(request)
        cache_data = memcache.get(cache_key)
        if cache_data:
            return cache_data


        if 'latitude' in request.GET and 'longitude' in request.GET:
            lat = float(request.GET['latitude'])
            lon = float(request.GET['longitude'])

            current_date = datetime.datetime.now().date()

            q = Venue.all()
            q.filter('start_date <= ', current_date)

            venues = Venue.proximity_fetch(q, geotypes.Point(lat, lon), max_results=20, max_distance=1609)

            results = []
            for venue in [v if v.end_date >= current_date else None for v in venues]:
                if venue:
                    q = Template.all().filter('venue =', venue.key())
                    templates = q.run(batch_size=1000)

                    results = results + [t.to_dict() for t in templates]

            venue_response = paginated_response(results)
            memcache.add(cache_key, venue_response, 120)
            return venue_response

        elif 'category' in request.GET:
            category = request.GET['category']

            q = Template.all().filter('category =', category.lower())
            q.filter('venue =', None)
            templates = q.run(batch_size=1000)

            category_response = paginated_response([t.to_dict() for t in templates])
            memcache.add(cache_key, category_response, 120)
            return category_response
        else:
            templates = Template.all().filter('venue =', None).order('name')

            all_response = paginated_response([t.to_dict() for t in templates])
            memcache.add(cache_key, all_response, 120)
            return all_response


class CategoryHandler(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request):
        return [c for (c, n) in TemplateForm.CATEGORIES]
