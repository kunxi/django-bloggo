from django.contrib.sites.models import Site
from django.contrib.sites import models as site_app
from django.db.models.signals import post_syncdb

from djblets.siteconfig.models import SiteConfiguration
from basic.blog.models import Post
import bloggo

def initial_siteconf(*args, **kwargs):
    print 'Initialize site configuration'

    siteconfig, created = SiteConfiguration.objects.get_or_create(site=Site.objects.get_current(), version=bloggo.__version__)
    if created:
        x = siteconfig.save()

post_syncdb.connect(initial_siteconf, sender=site_app)
