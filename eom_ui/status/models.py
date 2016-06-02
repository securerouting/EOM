# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [app_label]'
# into your database.
from __future__ import unicode_literals

from django.db import models
import datetime

class Cache(models.Model):
    cache_id = models.IntegerField(primary_key=True)
    host = models.TextField()
    port = models.TextField()
    version = models.IntegerField(blank=True, null=True)
    nonce = models.IntegerField(blank=True, null=True)
    serial = models.IntegerField(blank=True, null=True)
    updated = models.IntegerField(blank=True, null=True)
    refresh = models.IntegerField(blank=True, null=True)
    retry = models.IntegerField(blank=True, null=True)
    expire = models.IntegerField(blank=True, null=True)

    def _get_roa_count(self):
        roas = Prefix.objects.filter(cache_id=self.cache_id)
        return len(roas)
    roa_count = property(_get_roa_count)

    def _get_updated_timestr(self):
        return datetime.datetime.fromtimestamp(self.updated).strftime('%Y-%m-%d %H:%M:%S')
    updated_str = property(_get_updated_timestr)

    def _get_age(self):
        now = int(datetime.datetime.now())
        return now - self.updated
    age = property(_get_age) 

    class Meta:
        managed = False
        db_table = 'cache'

class Prefix(models.Model):
    prefix_id = models.AutoField(primary_key=True)
    cache_id = models.IntegerField()
    asn = models.IntegerField()
    prefix = models.TextField()
    prefixlen = models.IntegerField()
    max_prefixlen = models.IntegerField()
    prefix_min = models.TextField(blank=True)
    prefix_max = models.TextField(blank=True)

    class Meta:
        managed = False
        db_table = 'prefix'

class Routerkey(models.Model):
    cache_id = models.IntegerField()
    asn = models.IntegerField()
    ski = models.TextField()
    key = models.TextField()

    class Meta:
        managed = False
        db_table = 'routerkey'


class RtrCache(models.Model):
    rtr_id = models.IntegerField(primary_key=True)
    device = models.TextField(unique=True)
    rtrupdt = models.IntegerField(blank=True, null=True)

    def _get_rib_count(self):
        routes = RtrRib.objects.filter(rtr_id=self.rtr_id)
        return len(routes)
    rib_count = property(_get_rib_count)

    def _get_rtrupdt_timestr(self):
        return datetime.datetime.fromtimestamp(self.rtrupdt).strftime('%Y-%m-%d %H:%M:%S')
    rtrupdt_str = property(_get_rtrupdt_timestr)

    def _get_age(self):
        now = int(datetime.datetime.now())
        return now - self.updated
    age = property(_get_age) 

    class Meta:
        managed = False
        db_table = 'rtr_cache'


class RtrRib(models.Model):
    rtr_id = models.IntegerField(primary_key=True)
    idx = models.IntegerField()
    status = models.TextField(blank=True)
    pfx = models.TextField()
    pfxlen = models.IntegerField()
    pfxstr_min = models.TextField()
    pfxstr_max = models.TextField()
    nexthop = models.TextField()
    metric = models.IntegerField(blank=True, null=True)
    locpref = models.IntegerField(blank=True, null=True)
    weight = models.IntegerField(blank=True, null=True)
    pathbutone = models.TextField(blank=True)
    orig_asn = models.IntegerField()
    route_orig = models.TextField(blank=True)

    class Meta:
        managed = False
        db_table = 'rtr_rib'

class ReportIndex(models.Model):
    report_id = models.AutoField(primary_key=True)
    report_hash = models.TextField()
    device = models.TextField()
    timestamp = models.IntegerField()

    def _get_invalid_count(self):
        routes = ReportDetail.objects.filter(report_hash=self.report_hash)
        tot = len(routes)
        invalid = 0
        for r in routes:
            if r.invalid == 'I':
                invalid += 1
        return invalid
    invalid = property(_get_invalid_count)

    def _get_timestamp_timestr(self):
        return datetime.datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')
    timestamp_str = property(_get_timestamp_timestr)

    class Meta:
        managed = False
        db_table = 'report_index'


class ReportDetail(models.Model):
    route_id = models.AutoField(primary_key=True)
    report_hash = models.TextField()
    invalid = models.TextField()
    status = models.TextField()
    pfx = models.TextField()
    pfxlen = models.TextField()
    pfxstr_min = models.TextField()
    pfxstr_max = models.TextField()
    nexthop = models.TextField()
    metric = models.TextField()
    locpref = models.TextField()
    weight = models.TextField()
    pathbutone = models.TextField()
    orig_asn = models.TextField()
    route_orig = models.TextField()

    class Meta:
        managed = False
        db_table = 'report_detail'

class Fconstraints(models.Model):
    fcons_id = models.AutoField(primary_key=True)
    route_id = models.TextField()
    host = models.TextField()
    port = models.TextField()
    asn = models.TextField()
    prefix = models.TextField()
    prefixlen = models.IntegerField()
    max_prefixlen = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'fconstraints'

