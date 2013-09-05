from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from hotsocket.models import Recharge


class RechargeResource(ModelResource):
    """
    msisdn => E.164 Int i.e 27721231234
    denomination =>

    multiple uploads:
    url:
        - /api/v1/hotsocket/recharge/
        - PATCH (Only use it for multiple post)
    data =
    {
                    "objects": [
                        {
                            "denomination": 10,
                            "product_code": "AIRTIME",
                            "notes": "Grassroots Random Winner",
                            "msisdn": 27821231231
                        },
                        {
                            "denomination": 50,
                            "product_code": "AIRTIME",
                            "notes": "Grassroots Random Winner 2",
                            "msisdn": 27821231232
                        }
                    ]
                }
    """
    class Meta:
        resource_name = "hotsocket/recharge"
        list_allowed_methods = ["put", "get", "post", "patch"]
        detail_allowed_methods = ["put"]
        authorization = Authorization()
        include_resource_uri = True
        always_return_data = True
        queryset = Recharge.objects.all()
