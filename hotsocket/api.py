from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from hotsocket.models import Recharge


class RechargeResource(ModelResource):
    """
    msisdn => E.164 Int i.e 27721231234
    denomination => 
    """
    class Meta:
        resource_name = "hotsocket/recharge"
        list_allowed_methods = ["post", "get"]
        authorization = Authorization()
        include_resource_uri = True
        always_return_data = True
        queryset = Recharge.objects.all()

