from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from status.models import ReportIndex, ReportDetail

def index(request):
    report_list = ReportIndex.objects.order_by('-report_id')
    context = { 'report_list': report_list }
    return render(request, 'status/index.html', context)

def detail(request, rep_id):
    routes = ReportDetail.objects.all()
    #routes = ReportDetail.objects.filter(report_id=rep_id)
    context = { 'routes': routes }
    return render(request, 'status/detail.html', context)
