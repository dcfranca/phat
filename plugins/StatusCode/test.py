from common.core import BaseTestCase
from common.core import AutoTest
import responses


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

        responses.add(responses.GET, "http://test.myurl.com/test404",
                      status=404)

        responses.add(responses.GET, "http://test.myurl.com/test500",
                      status=500)

        tests_suite = [
            {
                'comment': '1st: SUCCESS',
                'url': 'http://test.myurl.com/test1'
            },
            {
                'comment': '2nd: SUCCESS',
                'url': 'http://test.myurl.com/test1',
                'status_codes': [404, 200]
            },
            {
                'comment': '3th: FAIL',
                'url': 'http://test.myurl.com/test1',
                'status_codes': [301, 302]
            },
            {
                'comment': '4th: SUCCESS',
                'url': 'http://test.myurl.com/test1',
                'status_codes': [200]
            },
            {
                'comment': '5th: FAIL',
                'url': 'http://test.myurl.com/test404',
            },
            {
                'comment': '6th: FAIL',
                'url': 'http://test.myurl.com/test404',
                'status_codes': [200]
            },
            {
                'comment': '7th: SUCCESS',
                'url': 'http://test.myurl.com/test404',
                'status_codes': [200, 404]
            },
            {
                'comment': '8th: SUCCESS',
                'url': 'http://test.myurl.com/test500',
                'status_codes': [500]
            },
        ]

        AutoTest.load_plugins()
        bt = self.run_test_suite(tests_suite=tests_suite)

        self.assertEqual(bt.run_log[0]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[0]['errors']), 0)
        self.assertEqual(len(bt.run_log[0]['failures']), 0)
        self.assertEqual(bt.run_log[0]['comment'], '1st: SUCCESS')

        self.assertEqual(bt.run_log[1]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[1]['errors']), 0)
        self.assertEqual(len(bt.run_log[1]['failures']), 0)
        self.assertEqual(bt.run_log[1]['comment'], '2nd: SUCCESS')

        self.assertEqual(bt.run_log[2]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[2]['errors']), 0)
        self.assertEqual(len(bt.run_log[2]['failures']), 1)
        self.assertEqual(bt.run_log[2]['comment'], '3th: FAIL')

        self.assertEqual(bt.run_log[3]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[3]['errors']), 0)
        self.assertEqual(len(bt.run_log[3]['failures']), 0)
        self.assertEqual(bt.run_log[3]['comment'], '4th: SUCCESS')

        self.assertEqual(bt.run_log[4]['url'], 'http://test.myurl.com/test404')
        self.assertEqual(len(bt.run_log[4]['errors']), 0)
        self.assertEqual(len(bt.run_log[4]['failures']), 1)
        self.assertEqual(bt.run_log[4]['comment'], '5th: FAIL')

        self.assertEqual(bt.run_log[5]['url'], 'http://test.myurl.com/test404')
        self.assertEqual(len(bt.run_log[5]['errors']), 0)
        self.assertEqual(len(bt.run_log[5]['failures']), 1)
        self.assertEqual(bt.run_log[5]['comment'], '6th: FAIL')

        self.assertEqual(bt.run_log[6]['url'], 'http://test.myurl.com/test404')
        self.assertEqual(len(bt.run_log[6]['errors']), 0)
        self.assertEqual(len(bt.run_log[6]['failures']), 0)
        self.assertEqual(bt.run_log[6]['comment'], '7th: SUCCESS')

        self.assertEqual(bt.run_log[7]['url'], 'http://test.myurl.com/test500')
        self.assertEqual(len(bt.run_log[7]['errors']), 0)
        self.assertEqual(len(bt.run_log[7]['failures']), 0)
        self.assertEqual(bt.run_log[7]['comment'], '8th: SUCCESS')
