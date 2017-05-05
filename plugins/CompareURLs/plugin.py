import requests
from common.core import register_plugin
from common.core import AbstractPlugin
from common.core import logger
from requests.auth import HTTPBasicAuth
from Levenshtein import ratio
from typing import Dict

@register_plugin
class CompareURLsPlugin(AbstractPlugin):
    """
    Compare a url to another
    based on the given fuzzy ratio in the `fuzzy` option it determines whether there's an error or not
    """
    fuzzy = 1.0
    url2 = ''

    def should_run(self):
        data = self.item_options.get('compare_url')

        if data:
            if isinstance(data, Dict):
                self.fuzzy = data.get('fuzzy', 1.0)
                self.url2 = data.get('url')
                if not self.url2:
                    logger.debug('compare_url must contain a url')
                    return False
            else:
                logger.debug('compare_url must be a nested dictionary containing url and ratio properties')
                return False

            return True

        return False

    def check(self):
        headers = self.item_options.get('headers', {})
        cookies = self.item_options.get('cookies', {})
        username = self.global_options.get('username')
        password = self.global_options.get('password')

        r2 = requests.get(self.url2, headers=headers,
                          auth=HTTPBasicAuth(username, password), allow_redirects=True, cookies=cookies)

        logger.info("Comparing urls...")
        if self.fuzzy == 1.0:
            self.ok(self.response.text == r2.text,
                    'Urls don\'t have equal content: {tested} and {reference}'.format(tested=self.url,
                                                                                      reference=self.url2))
        else:
            actual_ratio = ratio(self.response.text, r2.text)
            self.ok(actual_ratio > self.fuzzy,
                    """
                    Urls don\'t have sufficiently similar content: {tested} and {reference} (expected {expected}, got {actual})
                    """
                    .format(
                        tested=self.url,
                        reference=self.url2,
                        expected=self.fuzzy,
                        actual=actual_ratio))

        return self.is_ok()
