PHAT: Pluggable HTTP Auto Testing
===============

Tool for simple HTTP test automation.

# About

**PHAT** was originally conceived in a Booking.com Hackathon.
This tool main goal is to a simple and easy way to test HTTP requests.
The core of the application just make HTTP requests and send the response to the *plugins* available.

The strength of the tool is in its plugins.
I'll detail each plugin below and how to use it.

# Installation instructions
Go to the directory you downloaded it and run: 
```shell 
python setup.py install
```
**pip:** coming soon


#Basic Usage
```shell
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
  -l, --use-https       Indicates wether it should open the links using https
  -x, --no-proxy        Indicates wether it should use proxy or not
  -o OUTPUT_FILENAME, --output-file=OUTPUT_FILENAME
                        The json file to output with your results
  -d DEBUG, --debug=DEBUG
                        The debug messages level (1-4)
  --tests-sequential    If true, tests will be run sequentially for easier
                        troubleshooting
  -J JUNIT_FILENAME, --junit-file=JUNIT_FILENAME
                        The JUnit format file to output with your results
  -z SELENIUM_BROWSER, --selenium-browser=SELENIUM_BROWSER
                        The selenium driver to use, one of ('chrome',
                        'firefox', 'phantomjs')
  -Z SELENIUM_BROWSER_PATH, --selenium-browser-path=SELENIUM_BROWSER_PATH
                        Path to the browser or driver executable to use with
                        Selenium
  -G SELENIUM_GRID_HUB, --selenium-grid=SELENIUM_GRID_HUB
                        URL to connect on a Selenium Grid Hub
  --selenium-tests-sequential
                        If true, selenium tests will be run sequentially for
                        easier troubleshooting
  -H HTML_FILENAME, --html-file=HTML_FILENAME
                        The HTML format file to output with your results

```

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
Every other attribute is optional and depends on the plugins available.

