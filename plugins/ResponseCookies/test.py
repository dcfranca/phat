from common.core import BaseTestCase
import responses


class ResponseCookiesTestCase(BaseTestCase):

    @responses.activate
    def test_run(self):


        responses.add(responses.GET, 'http://invalid/cookies',
                      adding_headers = {
                          "set-cookie": "foo=bar; " +
                                        "domain=.invalid; " +
                                        # "expires=Fri, 01-Jan-2055 00:00:00 GMT; " +
                                        "path=/; " +
                                        "" # "HttpOnly",
                      })


        self.assert_pass({
            "url": "http://invalid/cookies",
            "response_cookies": {
                "foo": {"==": "bar", "startswith": "ba", "contains": "a",
                        "endswith": "ar", "!=": "tea", "match_regex": "\Abar\Z",
                        "flags": {
                            "comment": {"==": None},
                            "name": {"==": "foo"},
                            "value": {"==": "bar"},
                            "domain_specified": {"==": False},
                            "domain_initial_dot": {"==": False},
                        }}
            }
        })

        self.assert_pass({
            "url": "http://invalid/cookies",
            "response_cookies": {
                "perl": {"exists": False}
            }
        })

        self.assert_fail({
            "url": "http://invalid/cookies",
            "response_cookies": {
                "foo": {"==": "nano", "startswith": "nano", "contains": "nano",
                        "endswith": "nano", "!=": "bar", "match_regex": "\\Anano\\Z",
                        "flags": {
                            "comment": {"==": "foo"},
                            "name": {"!=": "foo"},
                            "value": {"!=": "bar"},
                            "validity": {">": 200},
                            "domain_specified": {"in": [True, None]},
                            "domain_initial_dot": {"in": [True, None]},
                        }
                }
            }
        }, failure_count=12)

        self.assert_fail({
            "url": "http://invalid/cookies",
            "response_cookies": {
                "perl": {}
            }
        }, failure_count=1, failure_re="expected, but not found")
