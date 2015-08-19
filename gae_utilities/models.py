from __future__ import with_statement

from google.appengine.ext import db, blobstore
import cloudstorage as gcs
import os
import uuid
from google.appengine.api import app_identity
from google.appengine.api.images import get_serving_url

from django.http import HttpResponse

class BlobModel(db.Model):
    '''
    Superclass for models that store a blobfile
    '''
    image = blobstore.BlobReferenceProperty()
    mime_type = db.StringProperty()
    url = db.StringProperty()

    def upload_image(self, blob, filename):
        mime_type = 'image/png'
        if filename.split('.')[-1] == 'jpg' or filename.split('.')[-1] == 'jpeg':
            mime_type = 'image/jpeg'

        bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
        bucket = '/' + bucket_name
        filename_final = bucket + '/' + str(uuid.uuid4())

        # Create a GCS file with GCS client.
        with gcs.open(filename_final, 'w') as f:
            f.write(blob)
            f.close()
       
        # Blobstore API requires extra /gs to distinguish against blobstore files.
        blobstore_filename = '/gs' + filename_final

        # Get the file's blob key
        blob_key = blobstore.create_gs_key(blobstore_filename)
        # Store it
        self.image = blob_key
        self.mime_type = mime_type
        self.url = get_serving_url(blob_key)

    def get_blob_response(self):
        response = HttpResponse()
        response[blobstore.BLOB_KEY_HEADER] = self.image.key()

        if self.mime_type:
            response['Content-Type'] = self.mime_type
        else:
            response['Content-Type'] = "image/png"

        return response
