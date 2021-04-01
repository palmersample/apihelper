"""
The ApiHelper class is essentially a wrapper for the Python 'requests'
library, but designed to utilize additional packages or tools to
honor API rate limiting strategies as well as session optimization
features.
"""
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests_toolbelt import sessions
import urllib3.exceptions


logger = logging.getLogger(__name__)

# Set a friendly timeout value for HTTP requests.  Don't set too low or
# you'll be a bad API user :)
REQUEST_TIMEOUT = 5  # Seconds

# Define a retry strategy to gracefully handle API rate limiting.
#
# There are numerous options, but a brief summary of those selected
# are below:
#
# total: Total number of retries to make.  After this is hit, expect
#        urllib3.exceptions.MaxRetryError exception to be raised.  Default
#        to 3 - change as desired.
#
# redirect: Maximum number of redirects to follow.  Used to control infinite
#           redirection loops
#
# backoff_factor: Specifies the multiplier used during graceful retry attempts
#                 calculated as:
#                 {backoff factor} * (2 ** ({number of total retries} - 1))
#
#                 For example, with a backoff factor of 1, retries will be
#                 0.5, 1, 2, 4, 8, 16 ... seconds between the next retry.
#                 I'm arbitrarily using 0.3, which results in a delay of:
#                 150, 300, 600, 1200, 2400 ... milliseconds.
#
# status_forcelist: The list of HTTP response codes which will result in a
#                   retry.
#
# allowed_methods: HTTP methods which will be retried.  The strategy here
#                  include all HTTP methods (even POST).  Should be safe
#                  to leave as-is, but modify as desired for your use case.
#
# respect_retry_after_header: Well, if the server says to wait, let's be a
#                             good citizen and wait...
#
# More info may be found at the urllib3 documentation site - current at time
# of code creation is:
# https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html
#
default_retry_strategy = Retry(
    total=3,
    redirect=16,
    backoff_factor=0.3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=[
        "HEAD", "GET", "PUT", "POST", "PATCH", "DELETE", "OPTIONS", "TRACE"
    ],
    respect_retry_after_header=True
)


# Decorator function to catch HTTP exceptions
def http_exceptions(func):
    def wrapper(*args, **kwargs):
        # Set a result first so it's not eaten in the event of exception
        wrapper_result = False
        try:
            # Make sure to assign this to a variable so we can properly return
            # at the end (returning 'method(...)' will result in calling the
            # method twice!
            wrapper_result = func(*args, **kwargs)
        except requests.exceptions.HTTPError as err:
            print(f"Http Error: {err}")
        except requests.exceptions.ConnectionError as err:
            print(f"Error Connecting: {err}")
        except requests.exceptions.Timeout as err:
            print(f"Timeout Error: {err}")
        except requests.exceptions.RequestException as err:
            print(f"Generic Request Exception: {err}")
        except requests.exceptions.RequestsWarning as err:
            print(f"HTTP: Request warning encountered: {err}")
        except urllib3.exceptions.MaxRetryError as err:
            print(f"HTTP: Max retries reached, request failed: {err}")
        # If you return the method as below, the request will be sent again
        # return method(self, *args, **kwargs)
        # Instead, return the result of the method_wrapper so the result isn't
        # eaten in this decorator.  Without this return statement, a caller
        # will only receive "None" on return from the called method from this
        # class.
        return wrapper_result
    return wrapper


class TimeoutHTTPAdapter(HTTPAdapter):
    """
    Extends the HTTPAdapter class to set a timeout for requests Session
    objects.  When used for a session, set the timeout to the value of
    REQUEST_TIMEOUT by default.  This will be overridden if the
    'timeout' argument is supplied.
    """
    def __init__(self, *args, **kwargs):
        self.timeout = REQUEST_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get('timeout')
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


class ApiHelper:
    """
    Class to wrap common 'requests' tasks, but with added sizzle!

    Tie the following features together:
      - Base URL sessions (a single session to a common base URL so subsequent
        requests may be made to a location relative to the base url)
      - Set a timeout for HTTP requests
      - Apply a rate-limit-friendly retry strategy to be a friendly API
        consumer
      - Set authentication for the HTTP session
      - For each HTTP request, raise for status and handle thrown exceptions
    """
    def __init__(self, baseurl=None, auth=None):

        # Hook for HTTP responses - raise each response for status so we can
        # gracefully handle thrown exceptions
        def assert_status_hook(response, *args, **kwargs):
            return response.raise_for_status()

        # Start a Base URL session if requested
        if baseurl:
            self.http = sessions.BaseUrlSession(base_url=baseurl)
        else:
            self.http = requests.Session()

        # Mount the TimeoutHTTPAdapter with retry strategy for both http and
        # https
        self.http.mount("https://", TimeoutHTTPAdapter(max_retries=default_retry_strategy))
        self.http.mount("http://", TimeoutHTTPAdapter(max_retries=default_retry_strategy))

        # Assign the response hook to the session
        self.http.hooks['response'] = [assert_status_hook]

        # And configure authentication for the session if requested
        if auth:
            self.http.auth = auth

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup - terminate the request session
        self.http.close()

    # HTTP Verb methods below:
    # NOTE - there's probably a better way to do this, but it was simple
    # enough to grab the common / listed verbs from the requests docs
    # and recreate here.  The following methods are mirrors of the same
    # as supplied in the 'requests' library.
    # Note the decorator for each method which takes us to the graceful
    # exception handler defined above this class.
    @http_exceptions
    def get(self, url, params=None, **kwargs):
        return self.http.get(url, params=params, **kwargs)

    @http_exceptions
    def options(self, url, **kwargs):
        return self.http.options(url, **kwargs)

    @http_exceptions
    def head(self, url, **kwargs):
        return self.http.head(url, **kwargs)

    @http_exceptions
    def post(self, url, data=None, json=None, **kwargs):
        # print(f"Starting POST operation with data:\n{data}")
        # print(f"Starting JSON POST with data:\n{json}")
        return self.http.post(url, data=data, json=json, **kwargs)

    @http_exceptions
    def put(self, url, data=None, **kwargs):
        return self.http.put(url, data=data, **kwargs)

    @http_exceptions
    def patch(self, url, data=None, **kwargs):
        return self.http.patch(url, data=data, **kwargs)

    @http_exceptions
    def delete(self, url, **kwargs):
        return self.http.delete(url, **kwargs)
