from common.core import register_plugin
from common.core import AbstractPlugin
from common.core import logger
from common.core import replace_vars
import time
import re
import urllib
import threading

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

OPERATORS = {
    '==': lambda x, y: x == y,
    'contains': lambda x, y: x.find(y) > -1,
    'startswith': lambda x, y: x.startswith(y),
    'endswith': lambda x, y: x.endswith(y)
}

# RPM installation will change this to True if detects firefox 46+
USE_MARIONETTE = False

def get_firefox_driver(path = None, selenium_grid_hub = None, no_proxy=False):

    if selenium_grid_hub:
        desired_capabilities={
            "browserName": "firefox",
            "javascriptEnabled": True,
            "proxy": {
                "proxyType": "direct" if no_proxy else "system"
            }
        }

        profile = webdriver.FirefoxProfile()
        profile.set_preference("network.http.phishy-userpass-length", 255);

        return webdriver.Remote(command_executor=selenium_grid_hub, desired_capabilities=desired_capabilities, browser_profile=profile)
    else:
        binary = None
        if path:
            binary = FirefoxBinary(path) #, log_file=open("/tmp/bat_firefox", 'a'))
        profile = webdriver.FirefoxProfile()
        profile.set_preference("network.http.phishy-userpass-length", 255);
        profile.set_preference("network.proxy.type", 0)
        capabilities = None
        if USE_MARIONETTE:
            # tell webdriver to use Marionette instead of plain Firefox
            capabilities = DesiredCapabilities.FIREFOX
            capabilities["marionette"] = True
        return webdriver.Firefox(firefox_profile=profile, firefox_binary=binary, capabilities=capabilities)


def get_chrome_driver(path=None, selenium_grid_hub = None, no_proxy=False):
    if path:
        return webdriver.Chrome(executable_path=path)
    else:
        return webdriver.Chrome()


def get_phantomjs_driver(path=None, selenium_grid_hub = None, no_proxy=False):
    if path:
        return webdriver.PhantomJs(executable_path=path)
    else:
        return webdriver.PhantomJs()


@register_plugin
class SeleniumPlugin(AbstractPlugin):

    sequential_testing_lock = threading.Lock()
    drivers = {
        'phantomjs': get_phantomjs_driver,
        'chrome': get_chrome_driver,
        'firefox': get_firefox_driver,
    }

    def get_driver(self):
        driver = self.global_options.get('selenium_browser', 'firefox')
        exe_path = self.global_options.get('selenium_browser_path', None)
        selenium_grid_hub = self.global_options.get('selenium_grid_hub', None)
        no_proxy = self.global_options.get('no_proxy', False)

        if no_proxy is False:
            import os
            if 'http_proxy' in os.environ: del os.environ['http_proxy']
            if 'https_proxy' in os.environ: del os.environ['https_proxy']
            if 'HTTP_PROXY' in os.environ: del os.environ['HTTP_PROXY']
            if 'HTTPS_PROXY' in os.environ: del os.environ['HTTPS_PROXY']

        return self.drivers[driver](exe_path, selenium_grid_hub, no_proxy)

    @staticmethod
    def add_global_options(parser):
        parser.add_option("-z", "--selenium-browser", dest="selenium_browser", action="store", default="firefox",
                          type='choice', choices=list(SeleniumPlugin.drivers.keys()),
                          help="The selenium driver to use, one of {choices}".format(choices=tuple(SeleniumPlugin.drivers.keys())))
        parser.add_option("-Z", "--selenium-browser-path", dest="selenium_browser_path", action="store", default=None,
                          help="Path to the browser or driver executable to use with Selenium")
        parser.add_option("-G", "--selenium-grid", dest="selenium_grid_hub", action="store", default=None,
                          help="URL to connect on a Selenium Grid Hub")
        parser.add_option("--selenium-tests-sequential", dest="selenium_sequential", action="store_true", default=False,
                          help="If true, selenium tests will be run sequentially for easier troubleshooting")

    def prepare_url(self):
        self.url = replace_vars(self.url)
        auth_url = self.prepare_username_password_url()
        url_params = self.prepare_url_parameters()
        hidden_url = '*********@{0}'.format(self.url)
        if url_params:
            return "{0}?{1}".format(auth_url, url_params), "{0}?{1}".format(hidden_url, url_params)
        return auth_url, hidden_url

    def prepare_url_parameters(self):
        data = self.item_options.get('data', {})
        data = replace_vars(data)
        return urllib.parse.urlencode(data)

    def prepare_username_password_url(self):
        username = 'username' in self.global_options and self.global_options['username'] and urllib.parse.quote(self.global_options['username'], safe='') or None
        password = 'password' in self.global_options and self.global_options['password'] and urllib.parse.quote(self.global_options['password'], safe='') or None
        if username and password:
            logger.debug("Selenium: username -> {0}".format(username))
            scheme, url = self.url.split('://')
            return '{scheme}://{username}:{password}@{url}'.format(scheme=scheme, username=username, password=password, url=url)

        return self.url

    # Selenium Test starts from here
    def check(self):
        if self.global_options.get('selenium_sequential', False):
            with SeleniumPlugin.sequential_testing_lock:
                return self.__check()
        else:
            return self.__check()

    def __check(self):
        sequential = self.global_options.get('selenium_sequential', False)

        if sequential:
            logger.info("selenium: Now testing {comment}".format(comment=self.item_options.get('comment', None) or self.url))

        logger.debug("Getting Driver...")
        self.driver = self.get_driver()

        self.driver.implicitly_wait(5)
        self.driver.set_window_size(1366, 768)  # fixme

        prepared_url, hidden_url = self.prepare_url()

        logger.debug("Selenium URL: {0}".format(hidden_url))

        self.driver.get(prepared_url)

        for step in self.item_options['selenium_steps']:
            logger.debug("Selenium Step: " + str(step))

            if 'wait' in step:
                time.sleep(step['wait'])

            if 'element' in step:
                action = None
                wait = None
                must_be_displayed = False
                contains_regex = None

                if 'action' in step['element']:
                    action = step['element'].pop('action')
                if 'wait' in step['element']:
                    wait = step['element'].pop('wait')
                if 'contains_regex' in step['element']:
                    contains_regex = step['element'].pop('contains_regex')

                if 'must_be_displayed' in step['element']:
                    must_be_displayed = step['element'].pop('must_be_displayed')

                exists = True if 'exists' not in step['element'] or step['element']['exists'] else False

                SELECTOR_RULES = set(('id', 'name', 'class', 'css_selector'))
                if not set(step['element']) & SELECTOR_RULES: # no SELECTOR_RULES found
                    raise ValueError("typo in rule? expected one of {expected}, got instead {got}"
                                     .format(expected=list(SELECTOR_RULES), got=step['element'].keys()))

                for key, value in step['element'].items():
                    if key not in SELECTOR_RULES:
                        pass

                    elements = self.find_elements(self.driver, key, value)

                    if len(elements) == 0 and exists:
                        self.fail('Element {rule} not found'.format(rule=repr({key: value})))
                        self.driver.save_screenshot("/tmp/screenshot_selenium.png")
                    elif len(elements) > 0 and not exists:
                        self.fail('{num} element{plural} {rule} found, expected 0. The first read {text}'
                                  .format(num=len(elements), plural="s" if len(elements) > 1 else "", rule=repr({key: value}),
                                          text=repr(elements[0].text)))
                    else:
                        self.passed()

                    displayed_element = False
                    for element in elements:
                        if element:
                            if element.is_displayed():
                                displayed_element = True
                                if contains_regex:
                                    logger.debug("Selenium - Searching for regex: {0}".format(contains_regex))
                                    if not re.search(contains_regex, element.text) and \
                                       not re.search(contains_regex, element.get_attribute('value') or ''):
                                        self.fail('Regex "{regex}" not found'.format(regex=contains_regex))
                                    else:
                                        self.passed()

                                if action:
                                    if wait:
                                        time.sleep(wait)
                                    try:
                                        self.action(element, action)
                                        self.passed()
                                    except WebDriverException:
                                        self.fail('Error trying to interact with element {element}'.format(
                                            element=value))

                    if len(elements) > 0 and displayed_element is False:
                        if must_be_displayed:
                            self.fail('Element "{0}" is not displayed'.format(value))
                        if action:
                            self.fail('Element "{0}" not displayed, so we can\'t interact with it'.format(value))
                        else:
                            self.passed()
                    else:
                        self.passed()

            if 'current_url' in step:
                current_url = step['current_url']
                url_to_compare = self.driver.current_url.replace(self.global_options['domain'], '')

                for k in current_url.keys():
                    if k not in OPERATORS:
                        self.fail("Invalid operator on url: {operator}".format(operator=k))
                    elif not OPERATORS[k](url_to_compare, current_url[k]):
                        self.fail("Current url don't match: {url1} {operator} {url2}"
                            .format(url1=url_to_compare, operator=k, url2=current_url[k]))
                    else:
                        self.passed()

            if 'do_js' in step:
                statement = step['do_js']['statement']
                wait_until_true = step['do_js'].get('wait_until_true', False)
                result = None
                if not wait_until_true:
                    result, exception = self.do_js(statement)
                else:
                    now = time.time()
                    timeout_at = now + step['do_js'].get('timeout', 30)
                    poll_frequency = step['do_js'].get('poll_frequency', 1)
                    truth_found = False
                    while not truth_found and time.time() < timeout_at:
                        time.sleep(poll_frequency)
                        result, exception = self.do_js(statement)
                        truth_found = result or exception
                    if not truth_found:
                        self.fail("Timed out while waiting for Javascript statement {stm} to evaluate truthfully".format(stm=repr(statement)))
                # this is the part where we should plug into JSONApi to check result...

            #logger.debug("Errors so far: %s" % str(self.errors))

        self.driver.close()

        return self.is_ok()

    def find_elements(self, driver, key, value):
        logger.debug("Finding element key: {0}, value: {1}".format(key, value))

        elements = []

        try:
            if str(key).lower() == 'id':
                elements = driver.find_elements_by_id(value)
                self.passed()
            if str(key).lower() == 'class':
                elements = driver.find_elements_by_class_name(value)
                self.passed()
            elif str(key).lower() == 'css_selector':
                elements = driver.find_elements_by_css_selector(value)
                self.passed()
            elif str(key).lower() == 'xpath':
                elements = driver.find_elements_by_xpath(value)
                self.passed()
        except Exception as ex:
            logger.warn("Exception while finding element: {0}\n".format(str(ex)))
            return []

        logger.debug("Elements found: {0}\n".format(len(elements)))

        return elements

    def action(self, control, action):

        if control.is_enabled():
            if 'click' in action and action['click']:
                control.click()
            elif 'type' in action and action['type']:
                control.send_keys(action['type'])
                self.passed()
        else:
            self.fail('control is not enabled, so we cannot interact with it')

    def do_js(self, statement):
        try:
            return self.driver.execute_script(statement), None
        except WebDriverException as e:
            self.fail("Could not execute statement {stm}: {msg}".format(stm=repr(statement), msg=e.msg))
            logger.info(str(e))
            return (None, e)

    def should_run(self):
        return 'selenium_steps' in self.item_options and self.item_options['selenium_steps']
