# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StoreToken'
        db.create_table(u'celerytasks_storetoken', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('token', self.gf('django.db.models.fields.CharField')(max_length=120)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('expire_at', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'celerytasks', ['StoreToken'])


    def backwards(self, orm):
        # Deleting model 'StoreToken'
        db.delete_table(u'celerytasks_storetoken')


    models = {
        u'celerytasks.storetoken': {
            'Meta': {'object_name': 'StoreToken'},
            'expire_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['celerytasks']