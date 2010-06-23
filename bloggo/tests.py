from django.http import HttpResponse, Http404
from context_processors import siteconfig

from unittest import TestCase
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.test import Client

def siteconfig_view(request):
    c = RequestContext(request, {}, [siteconfig])
    try:
        x = c['siteconfig']
    except KeyError:
        raise Http404
    return HttpResponse('siteconfig context_processor works.', status=200)

class TestView(TestCase):
    def setUp(self):
        self.client = Client()

    def testSiteConfDecorator(self):
        response = self.client.get(reverse('test_siteconfig'))
        self.assertEqual(response.status_code, 200)

