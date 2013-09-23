# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RechargeFailed'
        db.create_table(u'recharge_rechargefailed', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('recharge_failed', self.gf('django.db.models.fields.related.ForeignKey')(related_name='recharge_failed', to=orm['recharge.Recharge'])),
            ('recharge_status', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('failure_message', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'recharge', ['RechargeFailed'])


    def backwards(self, orm):
        # Deleting model 'RechargeFailed'
        db.delete_table(u'recharge_rechargefailed')


    models = {
        u'recharge.recharge': {
            'Meta': {'object_name': 'Recharge'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'denomination': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'msisdn': ('django.db.models.fields.BigIntegerField', [], {}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'product_code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'recharge_system_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'reference': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True', 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
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
        },
        u'recharge.rechargefailed': {
            'Meta': {'object_name': 'RechargeFailed'},
            'failure_message': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recharge_failed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recharge_failed'", 'to': u"orm['recharge.Recharge']"}),
            'recharge_status': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['recharge']