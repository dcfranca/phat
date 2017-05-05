from common.core import register_ut
from common.core import BaseTestCase
from common.core import AutoTest
import responses


@register_ut
class InverseRegexTestCase(BaseTestCase):

    @responses.activate
    def test_run(self):

        responses.add(responses.GET, "http://test.myurl.com/test1",
                      body="""
                               <html>
                               <head>
                                <title>Hello 999 world</title>
                               <head>
                               <body>
                                  <a href='/test2' id="test2-link" class='myclass'>Link to page 2</button>
                                  <a href='/test3' id="test3-link" class='myclass'>Link to page 3</button>
                                  <a href='/test404' class='myclass'>NOT FOUND</button>
                               </body>
                               </html>
                               """)

        tests_suite = [
            {
                'comment': '1st: FAIL',
                'url': 'http://test.myurl.com/test1',
                'regex': ['Hello my world']
            },
            {
                'comment': '2nd: FAIL',
                'url': 'http://test.myurl.com/test1',
                'regex': ['Hello', 'WHATEVER', 'world']
            },
            {
                'comment': '3th: FAIL',
                'url': 'http://test.myurl.com/test1',
                'regex': ['Not me', '^Neither me$', '[oO]+[rR]+[Mm]+[eE]*', '\d+']
            },
            {
                'comment': '4th: FAIL',
                'url': 'http://test.myurl.com/test1',
                'not_regex': ['Not me', '^Neither me$', '[oO]+[rR]+[Mm]+[eE]*', '\d+']
            },
            {
                'comment': '5th: SUCCESS',
                'url': 'http://test.myurl.com/test1',
                'not_regex': ['Not me', '^Neither me$', '[oO]+[rR]+[Mm]+[eE]*']
            },
            {
                'comment': '6th: SUCCESS',
                'url': 'http://test.myurl.com/test1',
                'regex': ['Hello \\d{3} world']
            },
            {
                'comment': '7th: FAIL',
                'url': 'http://test.myurl.com/test1',
                'regex': ['Hello \\d{4} world']
            },
        ]

        AutoTest.load_plugins()
        bt = self.run_test_suite(tests_suite=tests_suite)

        self.assertEqual(bt.run_log[0]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[0]['errors']), 0)
        self.assertEqual(len(bt.run_log[0]['failures']), 1)
        self.assertEqual(bt.run_log[0]['comment'], '1st: FAIL')

        self.assertEqual(bt.run_log[1]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[1]['errors']), 0)
        self.assertEqual(len(bt.run_log[1]['failures']), 1)
        self.assertEqual(bt.run_log[1]['comment'], '2nd: FAIL')

        self.assertEqual(bt.run_log[2]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[2]['errors']), 0)
        self.assertEqual(len(bt.run_log[2]['failures']), 3)
        self.assertEqual(bt.run_log[2]['comment'], '3th: FAIL')

        self.assertEqual(bt.run_log[3]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[3]['errors']), 0)
        self.assertEqual(len(bt.run_log[3]['failures']), 1)
        self.assertEqual(bt.run_log[3]['comment'], '4th: FAIL')

        self.assertEqual(bt.run_log[4]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[4]['errors']), 0)
        self.assertEqual(len(bt.run_log[4]['failures']), 0)
        self.assertEqual(bt.run_log[4]['comment'], '5th: SUCCESS')

        self.assertEqual(bt.run_log[5]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[5]['errors']), 0)
        self.assertEqual(len(bt.run_log[5]['failures']), 0)
        self.assertEqual(bt.run_log[5]['comment'], '6th: SUCCESS')

        self.assertEqual(bt.run_log[6]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[6]['errors']), 0)
        self.assertEqual(len(bt.run_log[6]['failures']), 1)
        self.assertEqual(bt.run_log[6]['comment'], '7th: FAIL')
