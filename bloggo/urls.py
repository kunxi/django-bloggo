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
    url(r'siteconfig', view=tests.siteconfig_view, name='test_siteconfig'),
    (r'', include('basic.blog.urls')),
)

