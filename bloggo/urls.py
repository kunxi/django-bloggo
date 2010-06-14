from django.conf.urls.defaults import *
from django.conf import settings
from basic.blog.feeds import BlogPostsFeed, BlogPostsByCategory
import tests

feeds = {
    'latest': BlogPostsFeed,
    'categories': BlogPostsByCategory,
}

urlpatterns = patterns('',
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict' : feeds}),
    url(r'siteconf', view=tests.siteconf_view, name='test_siteconf'),
    (r'', include('basic.blog.urls')),
)

