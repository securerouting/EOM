from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from status.models import Cache, RtrCache, ReportIndex, ReportDetail, Fconstraints
from django.db.models import F
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse

def index(request):
    report_list = ReportIndex.objects.order_by('-report_id')
    context = { 'report_list': report_list }
    return render(request, 'status/index.html', context)

def detail(request, rep_id):
    routes = []
    if ReportIndex.objects.all():
        ri = ReportIndex.objects.get(report_id=rep_id)
        if ri:
            routes = ReportDetail.objects.filter(report_hash=ri.report_hash)
    # Prep fields before display
    for r in routes:
        # Split the path into its constituent ASNs
        r.pathlist = r.pathbutone.split(' ')
        # Now find all the contstraints
        r.constraints = []
        constraints = Fconstraints.objects.filter(route_id=r.route_id)
        for c in constraints:
            r.constraints.append((c.asn, c.prefix, c.prefixlen, c.max_prefixlen))
    context = { 'routes': routes }
    return render(request, 'status/detail.html', context)

def devices(request):
    rtr_list = RtrCache.objects.order_by('rtr_id')
    rpki_server_list = Cache.objects.order_by('cache_id')
    context = { 'rtr_list': rtr_list, 'rpki_server_list': rpki_server_list }
    return render(request, 'status/devices.html', context)

# Provide an RSS Feed
class LatestEntriesFeed(Feed):

    title = "EOM latest reports"
    link = "/status/"

    def items(self):
        return ReportIndex.objects.order_by('-report_id')[:5]

    def item_title(self, item):
        return "TS:%s" % item.timestamp_str

    def item_description(self, item):
        return "Device:%s Invalid:%i"  % (item.device, item.invalid)

    def item_link(self, item):
        return reverse('status:detail', args=[item.report_id])
