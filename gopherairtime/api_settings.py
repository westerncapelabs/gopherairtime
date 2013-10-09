# This stores all the settings that will be used in the api

HOTSOCKET_BASE = "http://api.hotsocket.co.za:8080/"

HOTSOCKET_RESOURCES = {
    "login": "test/login",
    "recharge": "test/recharge",
    "status": "test/status",
    "statement": "test/statement",
    "balance": "test/balance",
}

HOTSOCKET_USERNAME = "trial_acc_1212"
HOTSOCKET_PASSWORD = "tr14l_l1k3m00n"

TOKEN_DURATION = 110  # Minutes


HOTSOCKET_CODES = {
    "SUCCESS": {"status": "0000", "message": "Successfully submitted recharge."},
    "TOKEN_INVALID": {"status": 887, "message": "Token is invalid , please login again to obtain a new one."},
    "TOKEN_EXPIRE": {"status": 889, "message": "Token has timed out , please login again to obtain a new one."},
    "MSISDN_NON_NUM": {"status": 6013, "message": "Recipient MSISDN is not numeric."},
    "MSISDN_MALFORMED": {"status": 6014, "message": "Recipient MSISDN is malformed."},
    "PRODUCT_CODE_BAD": {"status": 6011, "message": "Unrecognized product code, valid codes are AIRTIME, DATA, and SMS."},
    "NETWORK_CODE_BAD": {"status": 6012, "message": "Unrecognized network code."},
    "COMBO_BAD": {"status": 6020, "message": " Network code + Product Code + Denomination combination is invalid."},
    "REF_DUPLICATE": {"status": 6016, "message": "Reference must be unique."},
    "REF_NON_NUM": {"status": 6017, "message": "Reference must be a numeric value."},
}

HS_RECHARGE_STATUS_CODES = {
    "PENDING": {"code": 0 },
    "PRE_SUB_ERROR": {"code": 1},
    "FAILED": {"code": 2},
    "SUCCESS": {"code": 3},
}

INTERNAL_ERROR = {"LIMIT_REACHED": {"status": 404, "message": "Threshold Limit Reached."}}
