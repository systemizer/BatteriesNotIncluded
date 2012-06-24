"""
WSGI config for batteries project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os
import sys

from gevent import monkey
monkey.patch_all()

sys.path.insert(0,os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)) ,'..')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "batteries.settings")
os.environ['PYTHON_EGG_CACHE'] = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)) ,'.python-eggs'))

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)
