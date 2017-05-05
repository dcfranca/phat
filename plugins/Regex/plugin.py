from common.core import register_plugin
from common.core import AbstractPlugin
from common.core import logger
import re


@register_plugin
class RegexPlugin(AbstractPlugin):

    regex = []
    not_regex = []

    def search_regex(self, regexes, inverse=False):
        for rx in regexes:
            logger.debug("Regex - Searching regex: {0}".format(rx))
            if re.search(rx, self.response.text):
                logger.debug("Regex found")
                self.ok(inverse is False, 'Regex {0} found in html output'.format(rx))
            else:
                logger.debug("Regex not found")
                self.ok(inverse, 'Regex {0} not found in html output'.format(rx))

    def should_run(self):
        self.regex = self.item_options.get('regex', [])
        self.not_regex = self.item_options.get('not_regex', [])
        return len(self.regex) > 0 or len(self.not_regex) > 0

    def check(self):
        self.search_regex(self.regex)
        self.search_regex(self.not_regex, inverse=True)
        return self.is_ok()
