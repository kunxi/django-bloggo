from djblets.siteconfig.models import SiteConfiguration

def siteconf_processor(request):
    return {'siteconf': SiteConfiguration.objects.get_current() }
