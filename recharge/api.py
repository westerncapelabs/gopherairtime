from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from recharge.models import Recharge
from tastypie.authentication import ApiKeyAuthentication
from tastypie.http import HttpUnauthorized
import json


class OverrideApiAuthentication(ApiKeyAuthentication):
    def _unauthorized(self):
        data = json.dumps({"error": "You are not authorized"})
        return HttpUnauthorized(content=data, content_type="application/json; charset=utf-8")


class RechargeResource(ModelResource):
    """
    msisdn => E.164 Int i.e 27721231234
    denomination =>

    multiple uploads:
    url:
        - /api/v1/recharge/?username=""&api_key=""
        - PATCH (Only use it for multiple post)
    data =
    {
                    "objects": [
                        {
                            "denomination": 10,  # In rcents
                            "product_code": "AIRTIME",
                            "notes": "Grassroots Random Winner",
                            "msisdn": 27821231231
                        },
                        {
                            "denomination": 50,
                            "product_code": "SMS",
                            "notes": "Grassroots Random Winner 2",
                            "msisdn": 27821231232
                        }
                    ]
                }
    """
    class Meta:
        resource_name = "recharge"
        list_allowed_methods = ["put", "get", "post", "patch"]
        detail_allowed_methods = ["put"]
        authentication = OverrideApiAuthentication()
        authorization = Authorization()
        include_resource_uri = True
        always_return_data = True
        queryset = Recharge.objects.all()

