from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from status.models import ReportIndex, ReportDetail, Fconstraints
from django.db.models import F

def index(request):
    report_list = ReportIndex.objects.order_by('-report_id')
    context = { 'report_list': report_list }
    return render(request, 'status/index.html', context)

def detail(request, rep_id):
#    routes = ReportDetail.objects.all()
    routes = ReportDetail.objects.filter(report_id=rep_id)
    # Prep fields before display
    for r in routes:
        r.path = u'\u27a1'.join(r.pathbutone.split(' ')) + u'\u27a1' + r.orig_asn
        if r.invalid == 'V':
            # green check mark
            r.invalid = u'\u2705'
        elif r.invalid == 'I':
            # red check mark
            r.invalid = u'\u274c'
        else:
            # question mark
            r.invalid = u'\u003f'
        # Now find all the contstraints
        r.constraints = []
        constraints = Fconstraints.objects.filter(route_id=r.route_id)
        for c in constraints:
            r.constraints.append((c.asn, c.prefix, c.prefixlen, c.max_prefixlen))
    context = { 'routes': routes }
    return render(request, 'status/detail.html', context)
