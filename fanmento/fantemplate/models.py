from google.appengine.ext.db import to_dict
from google.appengine.ext import db

from geo.geomodel import GeoModel

from gae_utilities.models import BlobModel


class Venue(GeoModel):
    name = db.StringProperty()
    address = db.PostalAddressProperty()
    start_date = db.DateProperty()
    end_date = db.DateProperty()

    def date_string(self):
        start_date = self.start_date.strftime("%m/%d/%Y")
        end_date = self.end_date.strftime("%m/%d/%Y")

        return '%s - %s' % (start_date, end_date)

    def unlink_templates(self):
        templates = self.template_set
        for template in templates:
            template.venue = None
            template.put()

    def to_dict(self):
        result = to_dict(self)
        result['id'] = self.key().id()

        return result

    def delete(self):
        self.unlink_templates()
        super(Venue, self).delete()


class Advertisement(BlobModel):
    name = db.StringProperty()
    description = db.TextProperty()
    company = db.StringProperty()
    link = db.StringProperty()
    clicks = db.IntegerProperty()
    impressions = db.IntegerProperty()

    def unlink_templates(self):
        templates = self.template_set
        for template in templates:
            template.advertisement = None
            template.put()

    def delete(self):
        self.unlink_templates()
        super(Advertisement, self).delete()


class Background(BlobModel):
    name = db.StringProperty()
    description = db.TextProperty()

    def unlink_templates(self):
        templates = self.template_set
        for template in templates:
            template.background = None
            template.put()

    def delete(self):
        self.unlink_templates()
        super(Background, self).delete()


class Template(BlobModel):
    EFFECTS = (
        (0, 'Normal'),
        (1, 'Luma'),
        (2, 'Emboss'),
        (3, 'BlackWhite'),
        (4, 'Sepia'),
        (5, 'Toon'),
        (6, 'Threshold'),
        (7, 'Adaptive'),
        (8, 'Posterize'),
        (9, 'PolkaNil'),
        (10, 'PolkaMedium'),
        (11, 'PolkaLarge'),
        (12, 'Crosshatch'),
        (13, 'TrueBlue'),
        (14, 'NavyBlue'),
        (15, 'BullsRed'),
        (16, 'Gold'),
        (17, 'Yellow'),
        (18, 'HotOrange'),
        (19, 'TrueOrange'),
        (20, 'LimeGreen'),
        (21, 'DarkGreen'),
        (22, 'Purple'),
    )

    name = db.StringProperty()
    category = db.CategoryProperty()
    product_id = db.StringProperty()
    description = db.TextProperty()
    effect = db.CategoryProperty()
    advertisement = db.ReferenceProperty(reference_class=Advertisement)
    venue = db.ReferenceProperty(reference_class=Venue)
    code = db.StringProperty()
    background = db.ReferenceProperty(reference_class=Background)
    twitter_message = db.TextProperty()
    facebook_message = db.TextProperty()
    email_message = db.TextProperty()
    client_name = db.StringProperty()

    def to_dict(self):
        result = to_dict(self)

        result['id'] = self.key().id()
        result['effect'] = int(result['effect'])

        try: 
            result['advertisement'] = to_dict(self.advertisement)
        except: result['advertisement'] = {}

        try: result['venue'] = to_dict(self.venue)
        except: result['venue'] = {}

        try:
            result['background'] = to_dict(self.background)
        except: result['background'] = {}

        try: del result['venue']['location_geocells']
        except: pass

        return result
