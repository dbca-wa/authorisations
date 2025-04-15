from django.db import connection
from django.http import HttpResponse


def index(request):
    cursor = connection.cursor()
    cursor.execute('''SELECT NOW()''')
    row = cursor.fetchone()
    return HttpResponse("Database datetime: " + str(row[0]))