from common.core import register_ut
from common.core import BaseTestCase
from common.core import AutoTest
import responses


@register_ut
class FollowLinksTestCase(BaseTestCase):

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

        responses.add(responses.GET, "http://test.myurl.com/test404",
                      status=404)

        tests_suite = [
            {
                'comment': '1st: FAIL',
                'url': 'http://test.myurl.com/test1',
                'follow_links': True
            },
            {
                'comment': '2nd: FAIL',
                'url': 'http://test.myurl.com/test1',
                'follow_links_fast': 0.95
            },

            {
                'comment': '3th: SUCCESS',
                'url': 'http://test.myurl.com/test2',
                'follow_links': True
            },
        ]

        AutoTest.load_plugins()
        bt = self.run_test_suite(tests_suite=tests_suite, global_options={'domain': 'http://test.myurl.com/'})

        self.assertEqual(bt.run_log[0]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[0]['errors']), 0)
        self.assertEqual(len(bt.run_log[0]['failures']), 1)
        self.assertEqual(bt.run_log[0]['comment'], '1st: FAIL')

        self.assertEqual(bt.run_log[1]['url'], 'http://test.myurl.com/test1')
        self.assertEqual(len(bt.run_log[1]['errors']), 0)
        self.assertEqual(len(bt.run_log[1]['failures']), 1)
        self.assertEqual(bt.run_log[1]['comment'], '2nd: FAIL')

        self.assertEqual(bt.run_log[2]['url'], 'http://test.myurl.com/test2')
        self.assertEqual(len(bt.run_log[2]['errors']), 0)
        self.assertEqual(len(bt.run_log[2]['failures']), 0)
        self.assertEqual(bt.run_log[2]['comment'], '3th: SUCCESS')
