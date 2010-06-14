from django.http import HttpResponse, Http404
from context_processors import siteconf_processor

from unittest import TestCase
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.test import Client

def siteconf_view(request):
    c = RequestContext(request, {}, [siteconf_processor])
    try:
        x = c['siteconf']
    except KeyError:
        raise Http404
    return HttpResponse('siteconf_processor works.', status=200)

class TestView(TestCase):
    def setUp(self):
        self.client = Client()

    def testSiteConfDecorator(self):
        response = self.client.get(reverse('test_siteconf'))
        self.assertEqual(response.status_code, 200)

