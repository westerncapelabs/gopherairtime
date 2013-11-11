class SentryException(Exception):
    """
    Adding SentryException class for extensebility
    """
    def __init__(self, msg):
        self.msg = msg

        super(SentryException, self).__init__(msg)


class RechargeException(Exception):
    def __init__(self, msg):
        self.msg = msg

        super(RechargeException, self).__init__(msg)


class TokenInvalidError(RechargeException):
    pass


class TokenExpireError(RechargeException):
    pass


class MSISDNNonNumericError(RechargeException):
    pass


class MSISDMalFormedError(RechargeException):
    pass


class BadProductCodeError(RechargeException):
    pass


class BadNetworkCodeError(RechargeException):
    pass


class BadCombinationError(RechargeException):
    pass


class DuplicateReferenceError(RechargeException):
    pass


class NonNumericReferenceError(RechargeException):
    pass
