from common.core import AbstractPlugin
from common.core import logger
from common.core import store_var, replace_vars
import re


class HTTPResponseHeaderPlugin(AbstractPlugin):

    def should_run(self):
        return 'response_headers' in self.item_options and self.item_options['response_headers']

    def check(self):

        for header_name, tests in self.item_options['response_headers'].items():

            exists = tests.get('exists', True)

            if not header_name in self.response.headers:
                self.ok(not exists, 'HTTP header {name!r} expected, but not found'.format(name=header_name))
                continue

            header_value = self.response.headers[header_name]

            for operator, param in tests.items():
                self.handle_op("HTTP header rule {header!r}".format(header=header_name),
                               header_value, operator, param)

        return self.is_ok()
