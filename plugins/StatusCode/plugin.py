from common.core import register_plugin
from common.core import AbstractPlugin
from common.core import logger


@register_plugin
class StatusCodePlugin(AbstractPlugin):

    status_codes = [200, 301, 302]

    def should_run(self):
        sc = self.item_options.get('status_codes')
        if sc:
            self.status_codes = sc
        return True

    def check(self):
        logger.debug("StatusCodePlugin: response status code: %i", self.response.status_code)
        if self.response.status_code not in self.status_codes:
            self.fail('Expected status code %s, found %i' % (
            ','.join(map(str, self.status_codes)), self.response.status_code))
        return self.is_ok()
