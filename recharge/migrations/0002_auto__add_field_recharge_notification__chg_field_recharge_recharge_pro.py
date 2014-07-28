# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Recharge.notification'
        db.add_column(u'recharge_recharge', 'notification',
                      self.gf('django.db.models.fields.CharField')(max_length=160, null=True, blank=True),
                      keep_default=False)


        # Changing field 'Recharge.recharge_project'
        db.alter_column(u'recharge_recharge', 'recharge_project_id', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['users.Project']))

    def backwards(self, orm):
        # Deleting field 'Recharge.notification'
        db.delete_column(u'recharge_recharge', 'notification')


        # Changing field 'Recharge.recharge_project'
        db.alter_column(u'recharge_recharge', 'recharge_project_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['users.Project']))

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'recharge.recharge': {
            'Meta': {'object_name': 'Recharge'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'denomination': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'msisdn': ('django.db.models.fields.BigIntegerField', [], {}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'notification': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'product_code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'recharge_project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recharge_project'", 'to': u"orm['users.Project']"}),
            'recharge_system_ref': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'reference': ('django.db.models.fields.BigIntegerField', [], {'default': '138315080441300L', 'unique': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'status_confirmed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
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
        },
        u'users.project': {
            'Meta': {'object_name': 'Project'},
            'budget': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'recharge_limit': ('django.db.models.fields.IntegerField', [], {}),
            'users_projects': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['recharge']