import requests

# Simple class for generic HTTP 'Bearer' auth.  When invoked and passed a
# token, will add a "Authorization: Bearer {token}" header for use by the
# Python 'requests' library.


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        """
        Class initialization

        :param token:
            String - the token argument will be used when creating the
            "Authorization" HTTP header upon instantiation.
        """
        # Assign the token to a class variable
        self.token = token

    def __call__(self, r):
        """
        When the BearerAuth class is called as a function (e.g. passed to a
        requests object), this function is executed and will set the
        "Authorization" HTTP header for the passed requests object

        :param r:
            Requests object which will have the "Authorization" header set

        :return:
            The passed requests object
        """
        r.headers["Authorization"] = "Bearer " + self.token
        return r
