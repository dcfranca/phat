PHAT: Pluggable HTTP Auto Testing
===============

Tool for simple HTTP test automation.

# About

**PHAT** was originally conceived in a Booking.com Hackathon.
This tool main goal is to a simple and easy way to test HTTP requests.
The core of the application just make HTTP requests and send the response to the *plugins* available.

The strength of the tool is in its plugins.
I'll detail each plugin below and how to use it.

A plugin is able to:
1. Add command line options
2. Change the way to handle and generate URLs from relative paths 
3. Analyse an HTTP request/response and infer whether it's failing or not.

The documentation for creating new plugins is coming soon :)

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

#Default Plugins
###*CompareURL*
Plugin for testing if the response content of a http request is the similar to other one
###How it works
    It looks for the property compare_url on the json item, this property is dictionary containing the url to compare and the fuzzy ratio you expect.
    This test only run in the case it finds this property

    You can define how similar the response contents might be using the property fuzzy in a float from 0-1
    0 = They can  be completely different
    1 = They must be exactly the same
###Example
```json
{
 "url": "/relativepath/",
    "compare_url": {
       "url": "https://mydomain.com/absolutepath/",
       "fuzzy": 0.9
    }
}
```
###*StatusCode*
Plugin for testing the response status code of a HTTP request.
###How it works
    It looks for the property status_codes on the json item, this property is an array of expected status codes.
    If nothing is assigned the default value is defined as:
    [200, 301, 302]
    This test always run    
###Example
```json
{
   "url": "http://mydomain.com",
   "status_codes": [404, 200]
}
```
###*RunBrowser*
Plugin that opens the url in the default browser
###How it works
    It looks for the property run_browser on the json item, this property is a boolean, if the property is true it opens the url in a new tab in your default browser
###Example
```json
{
 "url": "/checkme/",
 "run_browser": true
}
```
###*Regex*
Plugin that checks if a list of regex expressions are in the response content of the http request.
###How it works
    It looks for the property regex or not_regex on the json item, this property is a list of strings containing the regex expressions you want to find or not to find.
###Example
```json
{
  "url": "/showmeanumber",
  "regex": ["[-+]?[0-9]*\\.[0-9]+"]
}
```
###*FollowLinks*
Plugin that follow the links on the page, looking for a 404 or 500 error
###How it works
    It looks for the property follow_links  or follow_links_fast on the json item
    The property follow_links is a simple boolean indicating wether the tests should follow the links or not, in case it's true it'll follow all the links on the page and report any 404 or 500 error.
    The property follow_links_fast is a float similar to the fuzzy property of the CompareURLs plugin indicating how different the urls must be to go through them, in this case the tests can run much faster as it's not going through all the links, but only the ~different~ ones.
###Example
```json
{
  "url": "/givemesomelinks",
  "follow_links_fast": 0.60
}
```
###*Selenium*
Plugin that allows to add Selenium tests to your test case
###How it works
    It looks for the property selenium_steps on the json item, this property is a list of steps that can be performed by Selenium.
    You also can pass the --selenium-browser to the command line to choose the browser you want to run the tests (the default is phantomjs, but it works nicer with Firefox) 
    If you want to run against a Selenium grid you have to add the parameter --selenium-grid, i.e: http://localhost:4445/wd/hub
    Each test can have one or more of those properties:
    element: If you want to check if some element exists, check its value or interact with it.
    Each element can have one or more of this properties:


         class: Select the element based on a css class
         id:  Select the element based on an id
         css_selector: Select the element given a css_selector expression
         must_be_displayed: Boolean indicating wether the element must be displayed or not (default is false)
         exists: Boolean indicating wether you want to check if an elements exists or the opposite (default is true)
         action: Property indicating the action to be made in the selected element
                      Possible actions are click or type(to type in an input field): 
         current_url: Check if the current url is ==, contains, starstswith or the specific string
         wait: An integer indicating the number of seconds to wait until the next step      
         contains_regex:  Indicating if the selected element must contains a specific regex expression          
###Example
```json
[
  {
    "url": "/",
    "selenium_steps": [
      {
        "element": {
          "id": "logo_no_globe_new_logo"
        }
      },
      {
        "element": {
          "id": "non-existent-item",
          "exists": false
        },
        "current_url": {
          "==": "/"
        }
      },
      {
        "element": {
          "id": "ss",
          "action": {
            "type": "amsterdam"
          }
        }
      },
      {
        "wait": 3
      },
      {
        "element": {
          "css_selector": ".autocomplete-list",
          "action": {
            "click": true
          }
        }
      },
      {
        "element": {
          "css_selector": ".searchbox-button",
          "action": {
            "click": true
          }
        },
        "current_url": {
          "contains": "/myurl"
        }
      }
    ]
  },
  {
    "url": "/components/",
    "selenium_steps": [
      {
        "element": {
          "class": "currency",
          "action": {
            "click": true
          }
        }
      },
      {
        "wait": 2
      },
      {
        "element": {
          "id": "selectme",
          "contains": "USD"
        }
      },
      {
        "element": {
          "id": "converter",
          "contains_regex": "[0-9]+\\.[0-9]{2}"
        }
      }
    ]
  }
]
```
###*JSONApi*
Plugin that allows to add json api tests to your test case
###How it works
    It looks for the property json_path on the json item, this property is a dictionary with json paths to match and what to do with those matches
    Each match can be evaluated using one of those operators:
    
    Regular operators 
    ==, !=, >, >=, <, <=, startswith, endswith, contains, match_regex
    
    Store operators 
    store_var (store single value), store_length (store the lenght of the results), store_array (store the array of results)
    Suppose you need the output from a previous call to do the next request, or even you need to check some values in the future, you can store values in variables using one of the store operators
    Later you can access the variable value using "<<name>>" syntax.
     
    Array operators (those operators apply over an array of results from the json path)
    length_==, length_!=, length_>, length_<, length_>=, length_<=, any_==, any_!=, any_>, any_>=, any_<, any_<=
    By the default the regular operators apply to all elements found that match the json path, and will report any error found, except if you use one of the any_ operators, in that case it'll fail only if none of the items comparison match.
###Example
```json
[
  {
    "url": "/browser/log",
    "data": {
      "message": "test"
    },
    "json_path": {
      "$.status": {
        "==": "ok"
      },
      "$.channels[0]": {
        "==": "error"
      }
    }
  },
  {
    "url": "/browser/settings",
    "data": { "id":13903, "extension_id": "123" },
    "json_path": {
      "$.*": {
        "!=": null
      }
    }
  },
  {
    "url": "/browser/store",
    "data": { "caller_id": "72074579", "id": 13903, "url": "http://mydomain.com/test"},
    "json_path": {
      "$.context_id": {
        ">": 0,
        "store_var": "context_id"
      }
    }
  },
  {"wait": 8},
  {
    "url": "/browser/retrieve",
    "data": {"id":"72074579", "recipient_staff_id" : 13903},
    "json_path": {
      "$._context_id": {"==": "<<context_id>>"},
      "$.urls[0]":{"==": "http://mydomain.com/test"}
    }
  },
  {
    "url": "/browser/mark",
    "data": {"context_id":"<<context_id>>"},
    "json_path": {
      "$.status":{"==": "OK"}
    }
  },
  {
    "url": "/iso",
    "json_path": {
      "$.LON": {"==": "gb"},
      "$.DUB": {"==": "ie"},
      "$.SEA": {"==": "us"},
      "$.CBG": {"==": "gb"},
      "$.BCN": {"==": "es"}
    }
  }
]
```
###*TimeMe*
Plugin that checks if a request is taking longer than expected
###How it works
    It looks for the property timeme on the json item, this property is an object with the those possible properties:
    requests: Number of requests to perform (default to 5)
    limit_max: Limit for the maximum request time (in seconds)
    limit_avg: Limit for the average request time (in seconds)
###Example
```json
{
  "url": "/myslowpage",
  "timeme": {
      "requests": 10, 
      "limit_max": 0.6,
      "limit_avg": 0.45
  }
}
```

###*JUnit*
Plugin to generate a JUnit format file output, so it can be integrated with JUnit tools, i.e: Jenkins
###How it works
    To use it you just need to pass the argument -J <filename> to the command line
    -J JUNIT_FILENAME, --junit-file=JUNIT_FILENAME
    The JUnit format file to output with your results

###*HTMLoutput*
Plugin to generate a HTML format file output, and open it in a browser for a nicer visualization of the results
###How it works
    To use it you just need to pass the argument -H <filename> to the command line
    -H HTML_FILENAME, --html-file=HTML_FILENAME
    The HTML format file to output with your results
    
    