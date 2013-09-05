# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Recharge'
        db.create_table(u'hotsocket_recharge', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('msisdn', self.gf('django.db.models.fields.BigIntegerField')()),
            ('product_code', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('denomination', self.gf('django.db.models.fields.IntegerField')()),
            ('reference', self.gf('django.db.models.fields.BigIntegerField')(unique=True, null=True)),
            ('notes', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('hot_socket_ref', self.gf('django.db.models.fields.BigIntegerField')(null=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('status_confirmed_at', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'hotsocket', ['Recharge'])

        # Adding model 'RechargeError'
        db.create_table(u'hotsocket_rechargeerror', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('recharge_error', self.gf('django.db.models.fields.related.ForeignKey')(related_name='recharge_error', to=orm['hotsocket.Recharge'])),
            ('error_id', self.gf('django.db.models.fields.IntegerField')()),
            ('error_message', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('tries', self.gf('django.db.models.fields.IntegerField')()),
            ('last_attempt_at', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'hotsocket', ['RechargeError'])


    def backwards(self, orm):
        # Deleting model 'Recharge'
        db.delete_table(u'hotsocket_recharge')

        # Deleting model 'RechargeError'
        db.delete_table(u'hotsocket_rechargeerror')


    models = {
        u'hotsocket.recharge': {
            'Meta': {'object_name': 'Recharge'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'denomination': ('django.db.models.fields.IntegerField', [], {}),
            'hot_socket_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'msisdn': ('django.db.models.fields.BigIntegerField', [], {}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'product_code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'reference': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'status_confirmed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        u'hotsocket.rechargeerror': {
            'Meta': {'object_name': 'RechargeError'},
            'error_id': ('django.db.models.fields.IntegerField', [], {}),
            'error_message': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_attempt_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'recharge_error': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recharge_error'", 'to': u"orm['hotsocket.Recharge']"}),
            'tries': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['hotsocket']