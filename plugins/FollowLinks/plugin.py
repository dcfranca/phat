from common.core import AbstractPlugin
from common.core import logger
from bs4 import BeautifulSoup, SoupStrainer
from common.core import classReplacements
from requests.auth import HTTPBasicAuth
import requests
import concurrent.futures


class FollowLinksPlugin(AbstractPlugin):

    fast = False
    fuzzy = 1.0
    domain = ''
    headers = {}

    @staticmethod
    async def request(url, headers, params, username, password, cookies):
        requests.get(url, headers, params,
                     auth=HTTPBasicAuth(username, password), allow_redirects=True, cookies=cookies)

    def should_run(self):
        self.domain = self.global_options.get('domain', '')
        self.headers = self.global_options.get('headers', {})

        fl = self.item_options.get('follow_links')
        flf = self.item_options.get('follow_links_fast')

        if flf:
            self.fast = True
            self.fuzzy = flf

        return fl or flf

    def check(self):
        URLUtils = classReplacements.get_class('URLUtils')
        data = self.response.text
        logger.debug('Parsing the HTML response...')
        soup = BeautifulSoup(data, "html.parser", parse_only=SoupStrainer('a', href=True))
        base_url = URLUtils.get_url_base(self.url)

        links = []
        futures = []
        username = self.global_options.get('username')
        password = self.global_options.get('password')
        params = self.global_options.get('params')
        cookies = self.global_options.get('cookies')
        number_workers = 5

        with concurrent.futures.ThreadPoolExecutor(max_workers=number_workers) as executor:
            for link in soup.find_all('a'):
                link_url = link.get('href')
                format_url_follow = URLUtils.format_url(link_url, base_url, global_options=self.global_options)

                if format_url_follow:
                    link_relative = format_url_follow.replace(self.domain, '').split('?')[0]
                    if self.fast and URLUtils.similar_link_visited(link_relative, links, self.fuzzy):
                        continue
                    links.append(link_relative)
                    args = {
                        'allow_redirects': True
                    }
                    if self.headers:
                        args['headers'] = self.headers
                    if params:
                        args['params'] = self.params
                    if cookies:
                        args['cookies'] = self.cookies
                    if username and password:
                        args['auth'] = HTTPBasicAuth(username, password)

                    futures.append(executor.submit(requests.get,
                                                   format_url_follow,
                                                   **args
                                                   ))

        links_exceptions = 0
        links_accessed = 0
        for fut in futures:
            try:
                response = fut.result()
            except Exception as ex:
                links_exceptions += 1
                continue
            else:
                links_accessed += 1
                logger.debug("Response status code {0} for url: {1} ".format(response.status_code, response.url))
                if response is not None and response.status_code > 400:
                    self.fail("Server responded with status code {status}".
                              format(status=response.status_code),
                              url=response.url)
                else:
                    self.passed()

        logger.debug("Links accessed: {0}, Links failed with exception: {1}, Total: {2}".format(links_accessed, links_exceptions, len(futures)))

        return self.is_ok()
