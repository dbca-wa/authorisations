from django.db import connection
from django.http import HttpResponse


def db_now_view(request):
    cursor = connection.cursor()
    cursor.execute('''SELECT NOW()''')
    row = cursor.fetchone()
    return HttpResponse("Database datetime: " + str(row[0]))

