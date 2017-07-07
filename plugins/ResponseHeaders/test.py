from common.core import BaseTestCase
import responses


class ResponseHeadersTestCase(BaseTestCase):

    @responses.activate
    def test_run(self):

        responses.add(responses.GET, "http://invalid/cookies",
                      adding_headers = {
                          "foo": "bar",
                          "egg": "baz",
                      })

        self.assert_pass({
            "url": "http://invalid/cookies",
            "response_headers": {
                "foo": {"==": "bar", "startswith": "ba", "contains": "a",
                        "endswith": "ar", "!=": "tea", "match_regex": "\Abar\Z"}
            }
        })

        self.assert_pass({
            "url": "http://invalid/cookies",
            "response_headers": {
                "perl": {"exists": False}
            }
        })

        self.assert_fail({
            "url": "http://invalid/cookies",
            "response_headers": {
                "foo": {"==": "nano", "startswith": "nano", "contains": "nano",
                        "endswith": "nano", "!=": "bar", "match_regex": "\Anano\Z"}
            }
        }, failure_count=6)

        self.assert_fail({
            "url": "http://invalid/cookies",
            "response_headers": {
                "perl": {}
            }
        }, failure_count=1, failure_re="expected, but not found")
