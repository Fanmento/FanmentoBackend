Fanmento API
==================

## General notes

All calls currently require Basic HTTP Auth

=====
## Users
### Register a user
    /api/v1/user

    Method: POST

    Parameters:
    email - String
	password - String (optional)
	facebook_token - String (optional)
    name - String (optional, full name)

### Upload a photo
    /api/v1/user/image

    Method: POST

    Parameters:
	image - File

### Get all photos
    /api/v1/user/image

    Method: GET

    Parameters:
	page - Integer (optional)

## Templates
### List all venues
    /api/v1/templates/venue

    Method: GET

### List all categories
    /api/v1/templates/category

    Method: GET

### Get template for location/category
    /api/v1/templates/template

    Method: GET

    Passing no parameters will return all templates

    Parameters:
    latitude (optional) - double
    longitude (optional) - double
    category (optional) - string

### Get template with 5-digit code
    /api/v1/templates/template/:code

    Method: GET

### Get a template's image
    /api/v1/templates/template/:id/image

    Method: GET

### Get an advertisement's image
    /api/v1/templates/ad/:id/image

    Method: GET

### Password Reset
    /admin/users/reset/request
