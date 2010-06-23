from djblets.siteconfig.models import SiteConfiguration

def siteconfig(request):
    return {'siteconfig': SiteConfiguration.objects.get_current()}
