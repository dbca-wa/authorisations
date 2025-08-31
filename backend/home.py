from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def home_page(request):
    return HttpResponse("Hello world!")
