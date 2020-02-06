from django.views.generic import View
from django.http import HttpResponse


def logout(request):
    response = HttpResponse('Cookies Deleted')
    response.delete_cookie('JWT', path='/')
    return response
