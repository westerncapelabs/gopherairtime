# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Recharge.status'
        db.delete_column(u'recharge_recharge', 'status')

        # Adding field 'Recharge.recharge_status'
        db.add_column(u'recharge_recharge', 'recharge_status',
                      self.gf('django.db.models.fields.CharField')(max_length=20, null=True),
                      keep_default=False)

        # Adding field 'Recharge.check_airtime_status'
        db.add_column(u'recharge_recharge', 'check_airtime_status',
                      self.gf('django.db.models.fields.CharField')(max_length=20, null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Recharge.status'
        db.add_column(u'recharge_recharge', 'status',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=20),
                      keep_default=False)

        # Deleting field 'Recharge.recharge_status'
        db.delete_column(u'recharge_recharge', 'recharge_status')

        # Deleting field 'Recharge.check_airtime_status'
        db.delete_column(u'recharge_recharge', 'check_airtime_status')


    models = {
        u'recharge.recharge': {
            'Meta': {'object_name': 'Recharge'},
            'check_airtime_status': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'denomination': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'msisdn': ('django.db.models.fields.BigIntegerField', [], {}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'product_code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'recharge_status': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'recharge_system_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'reference': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True', 'null': 'True'}),
            'status_confirmed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        u'recharge.rechargeerror': {
            'Meta': {'object_name': 'RechargeError'},
            'error_id': ('django.db.models.fields.IntegerField', [], {}),
            'error_message': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_attempt_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'recharge_error': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recharge_error'", 'to': u"orm['recharge.Recharge']"}),
            'tries': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['recharge']