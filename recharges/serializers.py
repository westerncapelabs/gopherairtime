from django.contrib.auth.models import User, Group
from .models import Recharge
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class RechargeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Recharge
        fields = ('url', 'id', 'amount', 'msisdn','network_code')
