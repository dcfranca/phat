"""
Core classes and methods used both for main and plugins packages
"""
import logging
from threading import Thread, Condition
import requests
import re
import collections
from requests.auth import HTTPBasicAuth
import unittest
import os
import sys
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from json.decoder import JSONDecodeError
from requests import Session
from requests import Request
import json
import time
import pprint

import requests.exceptions
import concurrent.futures


FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('autotest')


class DictionaryWithTimeout(collections.MutableMapping):
    """A multi-threaded dictionary that reorders writes after reads.

    >>> import concurrent.futures
    >>> data = DictionaryWithTimeout()
    >>> tp = concurrent.futures.ThreadPoolExecutor()
    >>> def read(): return data["test"]
    >>> def write(): data["test"] = "yup"
    >>> future = tp.submit(read)
    >>> _ = tp.submit(read)
    >>> future.running()
    True
    >>> _ = tp.submit(write)
    >>> future.result()
    'yup'

    Please note: in this statement:

        nv = STORED_VARS[k] if k in STORED_VARS else None

    if k is not in STORED_VARS.storage, the statement will block
    in `k in STORED_VARS` and not in accessing `STORED_VARS[k]`.

    You may hit the timeout incorrectly if too many read() threads
    are submitted to a ThreadPool before you submit the write()
    thread.

    """

    def __init__(self, *args):
        self.conditions = {}
        self.storage = dict(*args)

    def __getitem__(self, key, *, timeout=30):
        if key in self.storage:
            return self.storage[key]
        else:
            if key in self.conditions:
                cond = self.conditions[key]
            else:
                self.conditions[key] = cond = Condition()
            with cond:
                cond.wait(timeout)
            return self.storage[key]

    def __setitem__(self, key, value):
        self.storage[key] = value
        if key in self.conditions:
            cond = self.conditions[key]
            with cond:
                cond.notifyAll()

    def __len__(self):
        return len(self.storage)

    def __iter__(self, *args, **kwargs):
        return self.storage.__iter__(*args, **kwargs)

    def __delitem__(self, key):
        return self.storage.__delitem__(key)


STORED_VARS = DictionaryWithTimeout()


def replace_vars(value, *, autonumify=False):
    if isinstance(value, dict):
        materialized = {}
        for k, v in value.items():
            materialized[k] = replace_vars(v)
        return materialized

    if isinstance(value, list):
        materialized = []
        for v in value:
            materialized.append(replace_vars(v))
        return materialized

    if type(value) is str:
        for var in re.findall("<<\\w+>>", value):
            k = var.replace('<<', '').replace('>>', '')
            nv = STORED_VARS[k] if k in STORED_VARS else None
            if nv is not None:
                value = value.replace(var, str(nv))

        if autonumify:
            try:
                return float(value)
            except Exception:
                pass

    return value


def store_var(name, value):
    STORED_VARS[name] = value
    return True


class ClassReplacements(object):
    def __init__(self):
        self.registry = {}

    def register_class(self, name, cls):
        self.registry[name] = cls

    def get_class(self, name):
        return self.registry[name] if name in self.registry else None


classReplacements = ClassReplacements()


# Decorator to register class replacement
def register_replacement(name):
    def wrap(cls):
        classReplacements.register_class(name, cls)
        return cls

    return wrap


class AutoTest(object):
    """
    Test website in an automated way
    """
    settings = {}  # type: Dict[str, str]
    run_log = []  # type: List[Dict[str, str]]
    username = ''
    password = ''
    role = ''
    server = ''

    def __init__(self, global_options):
        URLUtils = classReplacements.get_class('URLUtils')
        self.global_options = global_options

        self.username = self.global_options.get('username', self.get_username())
        self.password = self.get_option('password')
        self.use_https = self.get_option('use_https', False)
        self.domain = URLUtils.mount_domain_url(self.global_options)
        self.global_options['domain'] = self.domain
        self.global_options['params'] = URLUtils.mount_url_params(self.global_options)
        self.run_log = []

    @staticmethod
    def load_classes(kind: str):
        import pkgutil
        import importlib
        paths = []
        paths.append(os.path.join(os.path.dirname(__file__), "..", "plugins"))
        
        extra_path = os.getenv('PHAT_EXTRA_PLUGINS_DIR')
        if extra_path:
            extra_path = os.path.join(extra_path, "plugins")
            paths.append(extra_path)

        for path in paths:
            if path not in sys.path:
                sys.path.append(path)
      
        logger.debug("Loading {}s from {}: ".format(kind, paths))
        loaded_items = []
        
        for _, name, ispkg in pkgutil.walk_packages(path=paths):
            logger.debug("Loading {}: {}".format(kind, name))

            if ispkg:
                try:
                    module = importlib.import_module('{}.{}'.format(name, kind))
                except ImportError as ex:
                    logger.debug("Error importing module: {0} of kind: {1}".format(name, kind))
                else:
                    loaded_items.append(module)

        # TODO: Return the classes instead of modules
        return loaded_items

    @staticmethod
    def load_ut_classes():
        return AutoTest.load_classes('test')

    @staticmethod
    def load_plugins():
        return AutoTest.load_classes('plugin')

    def get_username(self):
        custom_username = URLUtils.get_custom_username(self.global_options)
        return custom_username or os.environ.get('USER', '')

    def get_option(self, name, default=None):
        self.global_options[name] = self.global_options[name] if name in self.global_options and self.global_options[
            name] else default
        return self.global_options[name]

    def include_files(self, filename):
        materialized_tests = []
        f = open(filename, encoding='utf-8')
        if f:
            try:
                settings = json.load(f)
            except JSONDecodeError as e:
                data = open(filename, 'r').read()
                print("{filename}:{line}:{col}: failed to decode json: {msg}".format(filename=filename, line=e.lineno,
                                                                                     col=e.colno, msg=e.msg))
                print("\tGave up here: {context} ←".format(
                    context=repr(data[max(0, e.pos - 40):e.pos + 1].translate(str.maketrans("\t\n", "  ")))))
                exit(1)

            tests = settings["tests"]
            it = iter(tests)
            for item in it:
                if 'include' in item:
                    inc_filename = item['include']
                    if not os.path.isabs(inc_filename):
                        base_path = os.path.dirname(filename)
                        inc_filename = os.path.join(base_path, inc_filename)
                    inc = self.include_files(inc_filename)
                    materialized_tests.extend(inc)
                else:
                    materialized_tests.append(item)

        return materialized_tests

    def load_test_cases(self, filename):
        self.settings = []
        try:
            self.settings = self.include_files(filename)
        except (TypeError, KeyError):
            logger.fatal("""
            Error loading file: {0}. Check the file content
            (Maybe you're forgetting to split into 2 sections: settings and tests?
            """.format(filename))
            return False
        return True

    @staticmethod
    def load_default_options(filename):
        f = open(filename)
        settings = {}
        if f:
            json_content = json.load(f)
            if "settings" in json_content:
                settings = json_content["settings"]

        return settings

    def run_tests(self, link_url, item_options={}, global_options={}):
        test_errors = []
        test_failures = []

        if not link_url:
            return {
                'url': '(none)',
                'status': 'ERROR',
                'comment': item_options.get('comment', ''),
                'errors': ["No url was provided for this test:\n{test}".format(test=item_options)],
                'failures': []
            }
        else:
            URLUtils = classReplacements.get_class('URLUtils')
            format_url = URLUtils.format_url(link_url, global_options=global_options)

            if format_url:

                request_data = {'format_url': format_url, 'global_options': global_options, 'item_options': item_options}

                PluginHelpers.run_method_for_each(
                    'prepare_request_data',
                    global_options,
                    item_options,
                    request_data
                )
                request = URLUtils.prepare_request(request_data)

                # for logging purposes only
                format_url = request_data['format_url']

                # Run the test itself
                plugins_classes = []
                for module in plugins:
                    plugins_names = [name for name in dir(module) if name.endswith('Plugin') and name != "AbstractPlugin"]
                    for name in plugins_names:
                        cls = module.__dict__[name]
                        plugins_classes.append(cls)
                    
                for cls in plugins_classes:
                    cls.on_before_tests()
                try:
                    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
                    s = Session()
                    # We need this to merge the proxy env vars
                    settings = s.merge_environment_settings(request.url, {}, None, False, None)
                    logger.debug("Sending request: {0}?{1}".format(request.url, request.body or ''))
                    timeout = item_options.get('timeout', global_options.get('timeout', 30))
                    response = s.send(request, timeout=timeout, allow_redirects=True, **settings)
                except requests.exceptions.ReadTimeout as e:
                    actual_url = format_url
                    if request.method == 'get':
                        actual_url = request.url
                    return {
                        'url': format_url,
                        'status': 'FAILURE',
                        'comment': item_options.get('comment', ''),
                        'errors': [],
                        'failures': [{"url": actual_url, "error": "Request timed out"}],
                    }
                except Exception as e:
                    e.exc_info = sys.exc_info()
                    test_errors.append(e)
                    print(u"\N{WARNING SIGN}", end="", flush=True)
                    return {
                        'url': format_url,
                        'status': 'ERROR',
                        'comment': item_options.get('comment', ''),
                        'errors': test_errors,
                        'failures': [],
                    }

                for cls in plugins_classes:
                    c = cls(format_url, global_options, item_options, response)
                    cls.on_before_tests()
                    if c.should_run():
                        try:
                            check_result = c.check()
                            if not check_result:
                                test_failures += c.errors
                                print(u"\N{HEAVY BALLOT X}", end="", flush=True)
                            else:
                                print(u"\N{HEAVY CHECK MARK}", end="", flush=True)
                        except Exception as e:
                            e.exc_info = sys.exc_info()
                            test_errors.append(e)
                            print(u"\N{WARNING SIGN}", end="", flush=True)

                for cls in plugins_classes:
                    cls.on_after_tests()

                status = 'PASS'
                if len(test_errors) > 0:
                    status = 'ERROR'
                if len(test_failures) > 0:
                    status = 'FAILURE'

                return {
                    'url': format_url,
                    'status': status,
                    'comment': item_options.get('comment', ''),
                    'errors': test_errors,
                    'failures': test_failures,
                }

    def run(self):
        PluginHelpers.run_method_for_each('on_start', self.global_options, self.run_log)
        max_workers = 1 if self.global_options.get('tests_sequential', False) else None
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        futures = []

        for set_item in self.settings:
            if 'url' in set_item:
                url = set_item['url']
                futures.append(executor.submit(self.run_tests, url, set_item, self.global_options))
            elif 'wait' in set_item:
                now = time.time()
                executor.shutdown(True)  # wait for all current jobs to stop
                then = time.time()
                wait_more = set_item['wait'] - (then - now)
                if wait_more > 0:
                    time.sleep(wait_more)
                executor = concurrent.futures.ThreadPoolExecutor()  # replace the executor
        executor.shutdown(True)  # wait for all current jobs to stop

        for future in futures:
            self.run_log.append(future.result())

        PluginHelpers.run_method_for_each('on_end', self.global_options, self.run_log)


class PluginHelpers(object):
    @staticmethod
    def run_method_for_each(method_name, *args, **kwargs):
        instances = kwargs.pop('instances', None)
        values = instances if instances else plugins
        for item in values:
            method = getattr(item, method_name, None)
            if callable(method):
                method(*args, **kwargs)


class AbstractPlugin(object):
    """
    Base class to perform the checks
    """
    errors = []  # type: List[Dict[str, str]]

    def __init__(self, url, global_options, item_options, response):
        self.url = url
        self.global_options = global_options
        self.item_options = item_options
        self.response = response
        self.fatal = False
        self.errors = []
        self.operators = self.get_operators()

    def should_run(self):
        return False

    def is_ok(self):
        return len(self.errors) == 0

    def check(self):
        return False

    def fail(self, message, *, url=None):
        if url is None:
            url = self.url
        url = replace_vars(url)
        self.errors.append({"url": url, "error": message})
        print("\N{BALLOT X}", end="", flush=True)

    def passed(self):
        print("\N{CHECK MARK}", end="", flush=True)

    # Test::More influence
    def ok(self, condition, message_on_fail, *, url=None):
        if not condition:
            self.fail(message_on_fail, url=url)
        else:
            self.passed()

    @classmethod
    def get_operators(cls):
        return {
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
            '>': lambda x, y: x is not None and x == float(x) and float(x) > float(y),
            '<': lambda x, y: x is not None and x == float(x) and float(x) < float(y),
            '>=': lambda x, y: x is not None and x == float(x) and float(x) >= float(y),
            '<=': lambda x, y: x is not None and x == float(x) and float(x) <= float(y),
            'startswith': lambda x, y: x.startswith(y),
            'endswith': lambda x, y: x.endswith(y),
            'contains': lambda x, y: y in x,
            'match_regex': lambda x, y: re.match(y, x),
            'in': lambda item, bag: item in bag,
            'store_var': lambda value, name: store_var(name, value),
        }

    def handle_op(self, rule_name: str, got, operator: str, expected, *,
                  url=None, extra_formats={},
                  failure_message_format_string="{class} rule {rule_name!r} failed, {got!r} {operator} {expected!r}",
                  error_message_format_string="{class} rule {rule_name!r} failed, unknown operator {operator!r}"):
        str_format = {
            "class": type(self).__name__,
            "rule_name": rule_name,
            "header": rule_name,
            "got": got,
            "operator": operator,
            "expected": expected,
            "url": url,
            "result": None,
        }
        if operator in self.operators:
            expected = replace_vars(expected)
            result = str_format["result"] = self.operators[operator](got, expected)
            self.ok(result,
                    failure_message_format_string.format(**str_format),
                    url=url)
        else:
            raise ValueError(error_message_format_string.format(**str_format))

    @classmethod
    def on_start(cls, global_options, run_log=None):
        """
        Run before any test to any element
        """
        pass

    @classmethod
    def on_end(cls, global_options, run_log=None):
        """
        Run after all tests to all elements
        """
        pass

    @classmethod
    def on_before_tests(cls):
        """
        Run before run the tests for the element
        """
        pass

    @classmethod
    def on_after_tests(cls):
        """
        Run after run the tests for the element
        """
        pass

    @staticmethod
    def prepare_request_data(global_options, item_options, request_data):
        """
        Customize request configuration before sending request.
        :param global_options is a dictionary with global options (command line mostly)
        :param item_options is a dictionary with current item (test item) data
        :param request_data is a dictionary with following items
            * format_url
            * http_method
            * cookies [optional]
            * headers [optional]
            * data [optional]
            * auth [optional]
        """
        pass


plugins = []


class BaseTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(self):
        global plugins
        plugins = AutoTest.load_plugins()

    def run_test_suite(self, tests_suite={}, global_options={}):
        bt = AutoTest(global_options)
        bt.settings = tests_suite
        bt.run()
        return bt

    def assert_pass(self, test):
        bt = self.run_test_suite(tests_suite=[test])
        self.assertEqual(len(bt.run_log), 1)
        if len(bt.run_log[0]['errors']):
            raise bt.run_log[0]['errors'][0]
        self.assertEqual(len(bt.run_log[0]['failures']), 0,
            "\n" + pprint.pformat([fail['error'] for fail in bt.run_log[0]['failures']]))

    def assert_fail(self, test, *, failure_re=None, failure_count=1):
        bt = self.run_test_suite(tests_suite=[test])
        self.assertEqual(len(bt.run_log), 1)
        if len(bt.run_log[0]['errors']):
            raise bt.run_log[0]['errors'][0]
        if failure_count is not None:
            self.assertEqual(len(bt.run_log[0]['failures']), failure_count,
                "\n" + pprint.pformat([fail['error'] for fail in bt.run_log[0]['failures']]))
        else:
            self.assertTrue(len(bt.run_log[0]['failures']) > 0, "No test failed")
        if failure_re:
            for failure in bt.run_log[0]['failures']:
                self.assertRegex(failure['error'], failure_re)

    @staticmethod
    def data_provider(data):
        """
        Run test func N=(len(data)) times providing data[i] as *args for each run
        :param data: list of list
        """
        def data_provider_decorator(func):
            def wrapper(self):
                for i in data:
                    func(self, *i)

            return wrapper
        return data_provider_decorator


class AsyncRequest(Thread):
    r = None  # type: requests.Response

    def __init__(self, url, headers={}, params={}, username=None, password=None, browser='', method='GET',
                 cookies=None):
        super(AsyncRequest, self).__init__()
        self.url = url
        self.headers = headers
        self.params = params
        self.username = username
        self.password = password
        self.method = method
        self.browser = browser
        self.cookies = cookies

    def run(self):
        try:
            self.r = requests.get(self.url, headers=self.headers, params=self.params,
                                  auth=HTTPBasicAuth(self.username, self.password), allow_redirects=True,
                                  cookies=self.cookies)
        except Exception as ex:
            logger.error("Error accessing url: " + self.url + " - " + str(ex))


@register_replacement('URLUtils')
class URLUtils(object):
    @staticmethod
    def add_global_options(parser):
        pass

    @staticmethod
    def get_url_base(url):
        """
        :param url: str
        :return the base url when it' a .html page, otherwise None
        """
        protocol, url = url.split('://')
        last_idx = len(url)

        for idx2 in [m.start() for m in re.finditer('/', url)]:
            last_idx = idx2

        return '{0}://{1}'.format(protocol, url[0:last_idx])

    @staticmethod
    def format_url(link_url, base_url='', global_options={}, query_params=None):

        if not base_url:
            base_url = URLUtils.mount_domain_url(global_options)

        if link_url.startswith('http'):
            return link_url

        # Trim leading/trailing dash
        base_url = base_url.strip("/")
        link_url = link_url.strip("/")

        return '{0}/{1}'.format(base_url, link_url)

    @staticmethod
    def mount_domain_url(global_options={}):
        return 'http://test.invalid.domain.com'

    @staticmethod
    def similar_link_visited(link_url, links, fuzzy):
        return False

    @staticmethod
    def mount_url_params(global_options):
        return ''

    @staticmethod
    def get_custom_username(global_options):
        return ''

    @staticmethod
    def prepare_request_data(global_options, item_options, args):
        pass

    @staticmethod
    def prepare_request(args):
        tmp = args.copy()
        format_url = tmp.pop('format_url')
        global_options = tmp.pop('global_options')
        item_options = tmp.pop('item_options')

        format_url = format_url.replace('http:', 'https:') if item_options.get('use_https') else format_url

        headers = global_options['headers'] = global_options.get('headers', {})
        cookies = global_options['cookies'] = global_options.get('cookies', {})

        http_method = item_options.get('method', 'get').lower()

        data = item_options.get('data', {})

        args = {}

        username = global_options.get('username', None)
        password = global_options.get('password', None)

        if global_options['headers']:
            args['headers'] = replace_vars(headers)
        if username and password:
            args['auth'] = HTTPBasicAuth(username, password)
        if data:
            args['data'] = replace_vars(data)
        if global_options['cookies']:
            args['cookies'] = replace_vars(cookies)

        format_url = replace_vars(format_url)

        req = Request(http_method, format_url, **args)
        req = req.prepare()

        return req

