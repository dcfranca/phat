PHAT: Pluggable HTTP Auto Testing
===============

Tool for simple HTTP test automation.

Installation instructions
Go to the directory you downloaded it and run: python
setup.py install

Dependencies: python-dev, lxml2 

It's recommended to install in a python virtualenv! http://docs.python-guide.org/en/latest/dev/virtualenvs/

Usage: phat [options] -f <filename>

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -f FILENAME, --file=FILENAME
                        The json file that contains your test cases
  -u USERNAME, --username=USERNAME
                        The username for a http basic authentication
  -p PASSWORD, --password=PASSWORD
                        The password for a http basic authentication or a file
                        with the password
  -l, --use-https       If specified, links will be opened over https
  -x, --no-proxy        If specified, proxy environment variables will be
                        ignored
  -o OUTPUT_FILENAME, --output-file=OUTPUT_FILENAME
                        The json file to output with your results
  -d DEBUG, --debug=DEBUG
                        The debug messages level (1-4)

Additional switches depend on the set of plugins currently available.

The file required to run is a json file follows this structure:

[
  {
    "url": "/path/"
  },
  {
    "url": "/relativepath/",
    "run_browser": true,
    "regex": ["[-+]?[0-9]*\\.[0-9]+"]
  },
  {
    "url": "/relativepath/",
    "compare_url": "https://mydomain.com/absolutepath/",
    "fuzzy": 1.0,
    "run_browser": true
  }
]

Each item of the array of the json is required to contain a url
property, this url can use a relative or absolute path, if it’s a
relative the domain will be mounted based on the server, your username
and role.
Every other attribute is optional.

Optional attributes

status_codes: An array of status codes expected retrieving the url (default to 200)

compare_url: Url to compare the html output with, this one must be in absolute path format.

fuzzy: How different can both urls be? 1 for not different at all, 0 for completely different (default to 1).

follow_links: Indicates whether it should follow the links in the page to look for 404 or 500 errors (default to false).

follow_links_fast: Indicates whether it should follow the links in the page to look for 404 or 500 errors, it should be a float number to indicate how different the urls can be (similar to fuzzy option), it compares only the relative url, not the domain or the parameters (default to false).

run_browser: Indicates whether it should open a real browser tab with the url (default to false).

regex: An array of regular expressions to test against the html output (to match)

not_regex: An array of regular expressions to test against the html output (to not match)

user_agent: The User agent string you want to emulate (default to the same as for Chrome browser)

https: Indicates whether is to access this url using https or not (default to the command line option -l or False)

no_proxy: Indicates that it's not to use proxy to access urls

cookies: Dictionary of the cookies you want to inject

comment: Comment to output after retrieve the url
