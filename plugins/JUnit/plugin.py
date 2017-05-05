from common.core import register_plugin
from common.core import AbstractPlugin
from common.core import logger


@register_plugin
class JUnitPlugin(AbstractPlugin):

    @staticmethod
    def add_global_options(parser):
        parser.add_option("-J", "--junit-file", dest="junit_filename",
                          help="The JUnit format file to output with your results")

    @classmethod
    def on_end(cls, global_options, run_log=None):
        if 'junit_filename' in global_options and global_options['junit_filename']:
            filename = global_options['junit_filename']
            f = open(filename, 'w')
            if f:
                logger.debug('Writing JUnit output to file {0}.'.format(filename))
                f.write('<testsuite tests="{0}">'.format(len(run_log)))
                for test in run_log:
                    url, failures, comment = test['url'], test['failures'], test['comment']
                    comment = "({0}) ".format(comment) if comment else ''
                    name = "{0}{1}".format(comment, url)
                    if len(failures) == 0:
                        f.write('<testcase classname="Test" name="{0}"/>'.format(name))
                    else:
                        f.write('<testcase classname="Test" name="{0}">'.format(name))
                        for failure in failures:
                            url, msg = failure['url'], failure['error']
                            f.write('<failure type="{0}">{1}</failure>'.format(url, msg))
                        f.write('</testcase>'.format(name))

                f.write('</testsuite>')
                f.close()
            else:
                logger.warn("Can't open the file {0}. Check your permissions.".format(filename))


