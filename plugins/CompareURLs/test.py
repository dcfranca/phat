from common.core import BaseTestCase
from common.core import AutoTest
import responses


class CompareURLsTestCase(BaseTestCase):

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

        responses.add(responses.GET, "http://test.myurl.com/test2",
                  body="""
                                    <html>
                                        <head>
                                            <title>Page 2</title>
                                        <head>
                                        <body>
                                            <p>My paragraph</p>
                                            <a href='/test3' id="test3-link" class='myclass'>Link to page 3</button>
                                        </body>
                                    </html>
                                    """)

        responses.add(responses.GET, "http://test.myurl.com/test3",
                      body="""
                              <html>
                                  <head>
                                      <title>Page 2</title>
                                  <head>
                                  <body>
                                      <p>My Paragraph</p>
                                      <a href='/test3' id="test3-link" class='myclass'>Link to page 3</button>
                                  </body>
                              </html>
                              """)

        tests_suite = [
            {
                'comment': 'First item: FAIL',
                'url': 'http://test.myurl.com/test1',
                'compare_url': 'http://test.myurl.com/test2',  # FAIL
            },
            {
                'comment': 'Second item: FAIL',
                'url': 'http://test.myurl.com/test1',
                'compare_url': {},  # FAIL
            },
            {
                'comment': 'Third item: FAIL',
                'url': 'http://test.myurl.com/test1',
                'compare_url': {'url': 'http://test.myurl.com/test2'},  # FAIL
            },
            {
                'comment': '4th item: SUCCESS',
                'url': 'http://test.myurl.com/test1',
                'compare_url': {'url': 'http://test.myurl.com/test1'},  # SUCCESS
            },
            {
                'comment': '5th item: SUCCESS',
                'url': 'http://test.myurl.com/test1',
                'compare_url': {'url': 'http://test.myurl.com/test2', 'fuzzy': 0.7},  # SUCCESS
            },
            {
                'comment': '6th item: FAIL',
                'url': 'http://test.myurl.com/test1',
                'compare_url': {'url': 'http://test.myurl.com/test2', 'fuzzy': 0.99},  # FAIL
            },
            {
                'comment': '7th item: SUCCESS',
                'url': 'http://test.myurl.com/test2',
                'compare_url': {'url': 'http://test.myurl.com/test3', 'fuzzy': 0.9}  # SUCCESS
            }
        ]

        AutoTest.load_plugins()
        bt = self.run_test_suite(tests_suite=tests_suite)

        self.assertEqual(bt.run_log[0]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[0]['errors']), 0)
        self.assertEqual(len(bt.run_log[0]['failures']), 0)
        self.assertEqual(bt.run_log[0]['comment'], 'First item: FAIL')

        self.assertEqual(bt.run_log[1]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[1]['errors']), 0)
        self.assertEqual(len(bt.run_log[1]['failures']), 0)
        self.assertEqual(bt.run_log[1]['comment'], 'Second item: FAIL')

        self.assertEqual(bt.run_log[2]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[2]['errors']), 0)
        self.assertEqual(len(bt.run_log[2]['failures']), 1)
        self.assertEqual(bt.run_log[2]['comment'], 'Third item: FAIL')

        self.assertEqual(bt.run_log[3]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[3]['errors']), 0)
        self.assertEqual(len(bt.run_log[3]['failures']), 0)
        self.assertEqual(bt.run_log[3]['comment'], '4th item: SUCCESS')

        self.assertEqual(bt.run_log[4]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[4]['errors']), 0)
        self.assertEqual(len(bt.run_log[4]['failures']), 0)
        self.assertEqual(bt.run_log[4]['comment'], '5th item: SUCCESS')

        self.assertEqual(bt.run_log[5]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[5]['errors']), 0)
        self.assertEqual(len(bt.run_log[5]['failures']), 1)
        self.assertEqual(bt.run_log[5]['comment'], '6th item: FAIL')

        self.assertEqual(bt.run_log[6]['url'], 'http://test.myurl.com/test2')
        self.assertEqual(len(bt.run_log[6]['errors']), 0)
        self.assertEqual(len(bt.run_log[6]['failures']), 0)
        self.assertEqual(bt.run_log[6]['comment'], '7th item: SUCCESS')
