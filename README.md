# apihelper
A set of API-friendly Python "requests" library wrappers

# Purpose:
After speaking with a close friend that's a data scientist and appeared to be hitting some rate limiting, we decided to look into being somewhat respectful of other products - and, more importantly, to avoid having a program fail due to unexpected responses.  Thus, the primary concerns were:

- To reduce time spent copying and pasting the same code each time I create a project requiring HTTP API calls.
- To be a better "API Citizen" and respect API rate limits
- To gracefully catch errors in a consistent way

# Usage:
This has been initially been designed as a submodule for any project which uses RESTful HTTP API requests.  At its heart is just a class acting as a wrapper for the Python 'requests' library.

To incorporate this in your own project, try adding it as a git submodule.

1. Start your project.
2. Grab this repo and add it as a submodule: `git submodule add https://github.com/palmersample/apihelper.git`
3. That will create the directory.  Now grab the code: `git submodule update --recursive`

You should now have the code present.  Give it a shot!  In your Python project, import the ApiHelper class and instantiate an object.  For example:

```
from apihelper import ApiHelper, BearerAuth

with ApiHelper(auth=BearerAuth(token="your API token here")) as var_name:
    result = var_name.get(url='https://example.com')
```

The class supports all 'requests' methods available at time of this writing, including:
- get
- options
- head
- post
- put
- patch
- delete

In fact, it's literally a wrapper for those available in requests.  If you know how to use the 'requests' library, you know how to use this helper.

# Parameters:
Currently, two parameters are supported:
## baseurl:
'baseurl' creates an HTTP session object with the specified URL as the base.  Any subsequent requests will be relative to the base.  For example:

```
from apihelper import ApiHelper

with ApiHelper(baseurl="https://example.com") as var_name:
    result = var_name.get(url="/some/relative/url/here")
```
This may be useful if you need to repeatedly contact the same host but with different content locations

## auth:
'auth' accepts an object of type 'requests.auth.AuthBase'

Currently, I've included a single 'auth' class in the src/auth directory named "BearerAuth."  Create any auth class as needed for your application and pass an object derived from that class to ApiHelper and you should be off to the races.
