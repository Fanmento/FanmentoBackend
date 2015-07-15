from django.http import HttpResponse

from piston.decorator import decorator
from piston.resource import Resource
from piston.utils import rc, FormValidationError

import json

def validate(v_form, operation='POST'):
    """ This fetches the submitted data for the form 
        from request.data because we always expect JSON data
        It is otherwise a copy of piston.util.validate.
    """
        
    @decorator
    def wrap(f, self, request, *a, **kwa):
        
        # Assume that the JSON response is in request.data
        # Probably want to do a getattr(request, data, None)
        #   and raise an exception if data is not found
        form = v_form(request.data)

        if form.is_valid():
            setattr(request, 'form', form)
            return f(self, request, *a, **kwa)
        else:
            raise FormValidationError(form)
    return wrap

class Resource(Resource):
    
    def form_validation_response(self, e):
        """
        Turns the error object into a serializable construct.
        All credit for this method goes to Jacob Kaplan-Moss
        """
        
        # Create a 400 status_code response
        # Serialize the error.form.errors object
        json_errors = json.dumps(
            dict(
                (k, map(unicode, v))
                for (k,v) in e.form.errors.iteritems()
            )
        )

        resp = HttpResponse(json_errors, status=400)
        return resp
