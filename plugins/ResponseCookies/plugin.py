from common.core import register_plugin
from common.core import AbstractPlugin
from common.core import logger
from common.core import store_var, replace_vars
import time
import re

OPERATORS = {
    '==': lambda x, y: x == y,
    '!=': lambda x, y: x != y,
    'startswith': lambda x, y: x.startswith(y),
    'endswith': lambda x, y: x.endswith(y),
    'contains': lambda x, y: x.contains(y),
    'match_regex': lambda x, y: re.match(y, x),
    'in': lambda item, bag: item in bag
}

ACTIONS = {
    'store_var': lambda value, name: store_var(name, value),
}


@register_plugin
class HTTPResponseCookiePlugin(AbstractPlugin):

    def should_run(self):
        return 'response_cookies' in self.item_options and self.item_options['response_cookies']

    def get_cookie(self, name): #WHAT.
        for cookie in self.response.cookies:
            if cookie.name == name:
                return cookie

    def check(self):

        for cookie_name, tests in self.item_options['response_cookies'].items():

            exists = tests.get('exists', True)

            if not cookie_name in self.response.cookies:
                self.ok(not exists, 'HTTP cookie {name!r} expected, but not found'.format(name=cookie_name))
                continue

            cookie_obj = self.get_cookie(cookie_name)

            for operator, param in tests.items():
                if operator == "flags":
                    # somewhat evil but necessary to access _rest and, by extension, HTTPOnly
                    # which is kind of the main reason why I want to look at attributes to begin with
                    cookie_attrs = vars(cookie_obj)
                    cookie_attrs.update(cookie_attrs["_rest"])
                    if cookie_attrs["expires"] is not None:
                        cookie_attrs["validity"] = cookie_attrs["expires"] - time.time()
                    else:
                        cookie_attrs["validity"] = None

                    # { # example of flags available here
                    #  'comment': None,
                    #  'comment_url': None,
                    #  'discard': False,
                    #  'domain': '.mydomain.com',
                    #  'domain_initial_dot': True,
                    #  'domain_specified': True,
                    #  'expires': 1499618160,
                    #  'validity': 86400,
                    #  'HTTPOnly': None,
                    #  'name': 'ux',
                    #  'path': '/',
                    #  'path_specified': True,
                    #  'port': None,
                    #  'port_specified': False,
                    #  'rfc2109': False,
                    #  'secure': False,
                    #  'value': 'i',
                    #  'version': 0
                    # }

                    for flag_name, tests in param.items():
                        for op, param in tests.items():
                            self.handle_op('flag {flag_name} of {cookie_name}'.format(flag_name=flag_name, cookie_name=cookie_name),
                                           cookie_attrs[flag_name], op, param)
                else:
                    self.handle_op('value of {cookie_name}'.format(cookie_name=cookie_name),
                                   cookie_obj.value, operator, param)

        return self.is_ok()
