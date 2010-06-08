from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'', include('basic.blog.urls')),
)
