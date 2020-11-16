from django.http import HttpResponse
from django.shortcuts import redirect


WWW_HOMEPAGE_URL = "https://www.howsmytrack.com/"


def logout(request):
    response = HttpResponse("Cookies Deleted")
    response.delete_cookie("JWT", path="/")
    return response


def redirect_to_www(request):
    """The root of the API webapp is of no interest; it's more than
    likely that the user actually wanted to go to the web homepage.
    """
    return redirect(WWW_HOMEPAGE_URL)
