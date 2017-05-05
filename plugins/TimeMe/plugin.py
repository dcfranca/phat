from common.core import register_plugin
from common.core import AbstractPlugin
from common.core import classReplacements
from functools import reduce

import timeit

URLUtils = classReplacements.get_class('URLUtils')


@register_plugin
class TimeMePlugin(AbstractPlugin):

    def should_run(self):
        return isinstance(self.item_options.get('timeme'), dict)

    def check(self):
        timeme = self.item_options['timeme']
        requests = timeme['requests'] if 'requests' in timeme else 5
        limit_max = timeme.get('limit_max')
        limit_avg = timeme.get('limit_avg')
        from requests import Session
        s = Session()
        request = URLUtils.prepare_request(self.url, self.global_options, self.item_options)
        times = timeit.repeat(stmt=lambda:s.send(request, timeout=30, allow_redirects=True),
                              repeat=requests, number=1)

        request_max = max(times)
        request_avg = reduce(lambda x, y: x + y, times) / len(times)

        if limit_max and request_max > limit_max:
            self.fail("Maximum request time greater than limit: {0} > {1}".format(request_max, limit_max))
        if limit_avg and request_avg > limit_avg:
            self.fail("Average request time greater than limit: {0} > {1}".format(request_avg, limit_avg))

        return self.is_ok()
