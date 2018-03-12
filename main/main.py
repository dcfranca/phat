import responses
import re
from Levenshtein import ratio
from optparse import OptionParser
from settings import VERSION
from requests.auth import HTTPBasicAuth

import sys
import os

from common.core import classReplacements
from common.core import logger
from common.core import PluginHelpers
from common.core import replace_vars
from common.core import AutoTest
import time
import json
from json.decoder import JSONDecodeError
import traceback
from requests import Request

sys.path.append(os.path.dirname(__file__))


class TestURLUtils(object):
    @staticmethod
    def add_global_options(parser):
        pass

    @staticmethod
    def get_url_base(url):
        """
        :param url: str
        :return the base url when it' a .html page, otherwise None
        """
        # idx = url.find('.html')
        # if idx < 0: return None
        last_idx = 0

        for idx2 in [m.start() for m in re.finditer('/', url)]:
            last_idx = idx2

        return url[0:last_idx]

    @staticmethod
    def format_url(link_url, base_url='', global_options={}):
        if not link_url: return ''

        link_url = link_url.replace('\n', '')
        link_url = link_url.replace('\t', '')

        format_url = None
        domain = URLUtils.mount_domain_url(global_options)
        if not base_url:
            base_url = domain

        if link_url.startswith('/'):
            format_url = domain + link_url
        elif '.html' in link_url and base_url and '://' not in link_url:
            format_url = base_url + link_url
        elif link_url.startswith('http://') or link_url.startswith('https://'):
            format_url = link_url

        return format_url

    @staticmethod
    def mount_domain_url(global_options={}):
        return 'http://test.myurl.com'

    @staticmethod
    def similar_link_visited(link_url, links, fuzzy):
        for link in links:
            if ratio(link_url, link) >= fuzzy:
                # Link already accessed, return
                return True
        return False

    @staticmethod
    def mount_url_params(global_options):
        return ''

    @staticmethod
    def get_custom_username(global_options):
        return None

    @staticmethod
    def prepare_request(format_url, global_options, item_options):
        # request expect that cookie values are str or None
        cookies = {}
        if item_options['cookies'] is not None:
            for k in item_options['cookies'].keys():
                if item_options['cookies'][k] is not None:
                    item_options['cookies'][k] = str(item_options['cookies'][k])
                cookies = item_options['cookies']

        format_url = format_url.replace('http:', 'https:') if 'use_https' in item_options and item_options[
            'use_https'] else format_url

        headers = {'User-Agent': item_options['user_agent']} if item_options['user_agent'] else {}

        if 'headers' in global_options:
            headers.update(global_options['headers'])

        if 'headers' in item_options:
            headers.update(item_options['headers'])

        global_options['headers'] = headers
        global_options['cookies'] = cookies

        http_method = item_options.get('method', 'get').lower()

        data = {}
        if 'data' in item_options and item_options['data']:
            data = item_options['data']

        args = {}

        username = global_options.get('username', None)
        password = global_options.get('password', None)

        if headers:
            headers = replace_vars(headers)
            args['headers'] = headers
        if username and password:
            args['auth'] = HTTPBasicAuth(username, password)
        if data:
            data = replace_vars(data)
            args['data'] = data
        if cookies:
            cookies = replace_vars(cookies)
            args['cookies'] = cookies

        req = Request(http_method, format_url, **args)
        req = req.prepare()

        return req


def test():
    import unittest
    ut_modules = AutoTest.load_ut_classes()
    suite = unittest.TestSuite()
    for module in ut_modules:
        classes = [name for name in dir(module) if name.endswith('TestCase') and name != "BaseTestCase"]
        for name in classes:
            cls = module.__dict__[name]
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))

    unittest.TextTestRunner().run(suite)


def main():
    # Run tests
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test()
        exit(0)

    """
    Manage all the CLI options
    """
    parser = OptionParser(usage='usage: %prog [options] -f <filename>', version="%prog {0}".format(VERSION))
    parser.add_option("-f", "--file", dest="filename", help="The json file that contains your test cases")
    parser.add_option("-u", "--username", dest="username", help="The username for a http basic authentication")
    parser.add_option("-p", "--password", dest="password",
                      help="The password for a http basic authentication or a file with the password")
    parser.add_option("-l", "--use-https", dest="use_https", action="store_true",
                      help="Indicates wether it should open the links using https")
    parser.add_option("-x", "--no-proxy", dest="no_proxy", action="store_true",
                      help="Indicates wether it should use proxy or not")
    parser.add_option("-o", "--output-file", dest="output_filename", help="The json file to output with your results")
    parser.add_option("-d", "--debug", dest="debug", type="int", default=3, help="The debug messages level (1-4)")
    parser.add_option("--tests-sequential", dest="tests_sequential", action="store_true", default=False,
                      help="If true, tests will be run sequentially for easier troubleshooting")

    # Add options from plugins
    AutoTest.load_plugins()

    global URLUtils
    URLUtils = classReplacements.get_class('URLUtils')

    # load custom cmd args we accept
    PluginHelpers.run_method_for_each('add_global_options', parser)

    if len(sys.argv) == 1:
        sys.argv.append('-h')

    (options, args) = parser.parse_args()

    if not options.filename:
        print("Filename is required to run PHAT!")
        exit(1)

    try:
        filename = options.filename
        global_options = AutoTest.load_default_options(filename)
    except JSONDecodeError as e:
        data = open(filename, 'r').read()
        print("{filename}:{line}:{col}: failed to decode json: {msg}".format(filename=filename, line=e.lineno,
                                                                             col=e.colno, msg=e.msg))
        print("\tGave up here: {context} ←".format(
            context=repr(data[max(0, e.pos - 40):e.pos + 1].translate(str.maketrans("\t\n", "  ")))))
        exit(1)

    if options.debug not in range(1, 5):
        options.debug = 1

    debug_level = 50 - (options.debug * 10)
    logger.setLevel(debug_level)

    if options.password and os.path.isfile(options.password):
        options.password = open(options.password).read().replace('\n', '')

    if options.username and options.password is None:
        from getpass import getpass
        # Ask for user to enter it
        options.password = getpass()

    if options.no_proxy:
        if 'http_proxy' in os.environ: del os.environ['http_proxy']
        if 'https_proxy' in os.environ: del os.environ['https_proxy']
        if 'HTTP_PROXY' in os.environ: del os.environ['HTTP_PROXY']
        if 'HTTPS_PROXY' in os.environ: del os.environ['HTTPS_PROXY']

    # # Retrieve all experients/variants data
    # experiments = options.experiments.split(',') if options.experiments and options.experiments.find(',') > -1 else [
    #     options.experiments]
    # variants = options.variants.split(',') if options.variants and options.variants.find(',') > -1 else [
    #     options.variants]
    #
    dict_options = {k: v for k, v in vars(options).items() if v is not None}

    global_options.update(dict_options)

    start = time.time()

    bt = AutoTest(global_options)

    # Load test cases
    if not bt.load_test_cases(filename):
        exit(1)

    bt.run()

    end = time.time()

    exit_status = 0

    print()
    print("------------------------------\n")
    print("**** FULL LOG ****")

    for log in bt.run_log:
        comment = ' (' + log['comment'] + ')' if 'comment' in log and log['comment'] else ''  # log['comment']
        print('\n{status}:{comment} {url}'.format(comment=comment, url=log['url'], status=log['status']))
        for error in log['errors']:
            print("ERROR: {cls}: {message} {tb}\n".format(url=log["url"],
                                                          cls=type(error).__name__,
                                                          message=error.msg if "msg" in dir(error) else error,
                                                          tb="\t\t".join(
                                                              line.replace("\n    ", "\n\t\t    ") for line in
                                                              traceback.format_exception(*error.exc_info)[:-1])))

        prev_url = log["url"]
        for failure in log['failures']:
            url_line = ''
            if 'url' in failure and failure['url'] != prev_url:
                url_line = "\n\tURL: {url}\n".format(url=replace_vars(failure['url']))
                prev_url = failure['url']
            print("{url_line}\tFAILURE: {message}".format(url_line=url_line,
                                                          message=failure['error']))

    if options.output_filename:
        f = open(options.output_filename, 'w')
        if f:
            results = json.dumps(bt.run_log, indent=4)
            print(results, file=f)
            f.close()

    print("\n--------------------------------")

    no_tests = len(bt.run_log)
    no_errors = len([x for x in bt.run_log if len(x['errors']) > 0])
    no_failures = len([x for x in bt.run_log if len(x['failures']) > 0])
    run_seconds = end - start

    if no_errors == 0 and no_failures == 0:
        print("| Test successfully completed! |")
    else:
        print("| Test failed!                 |")
        exit_status = 1
    print("--------------------------------")
    print("Ran {no_tests} test cases in {run_seconds:.2f} seconds, errors={no_errors} failures={no_failures}\n".format(
        no_tests=no_tests,
        run_seconds=run_seconds,
        no_errors=no_errors,
        no_failures=no_failures
    ))

    exit(exit_status)
