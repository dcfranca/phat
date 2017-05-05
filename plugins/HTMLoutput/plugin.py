from common.core import register_plugin
from common.core import AbstractPlugin
from common.core import logger
import webbrowser
import os

@register_plugin
class HTMLPlugin(AbstractPlugin):

    @staticmethod
    def add_global_options(parser):
        parser.add_option("-H", "--html-file", dest="html_filename",
                          help="The HTML format file to output with your results")

    @classmethod
    def on_end(cls, global_options, run_log=None):
        if 'html_filename' in global_options and global_options['html_filename']:
            filename = global_options['html_filename']
            f = open(filename, 'w')
            if f:
                logger.debug('Writing HTML output to file {0}.'.format(filename))
                f.write("""
                <html>
                    <head>
                        <meta charset="UTF-8">
                        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/1.11.8/semantic.min.css"/>
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.1.3/jquery.min.js"></script>
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/1.11.8/semantic.min.js"></script>
                        <title>PHAT Results</title>
                    </head>
                    <body>
                        <h2 class="ui center aligned icon header">
                          <i class="circular lab icon"></i>
                          Test Results
                        </h2>
                        <div class="ui column grid" style="margin-left: 10">
                            <div class="column">
                                <div class="ui cards">
                """)
                for test in run_log:
                    url, failures, comment = test['url'], test['failures'], test['comment']
                    name = comment if comment else url
                    f.write("<div class='card'>")

                    icon, color = ("remove", "red") if len(failures) > 0 else ("check", "green")

                    f.write("""
                    <div class="content">
                        <i class="{icon} {color} circle icon right floated"></i>
                        <div class="meta">{name}</div>
                    </div>
                    """.format(name=name, icon=icon, color=color))

                    f.write("<div class='extra content'>")
                    if failures:
                        for failure in failures:
                            url, msg = failure['url'], failure['error']
                            f.write("""
                                <a href="{url}"><button class="ui red button">{msg}</button></a>
                            """.format(url=url, msg=msg))
                    else:
                        f.write("""
                            <a href="{url}"><button class="ui green button">All tests passed!</button></a>
                        """.format(url=url))

                    f.write("</div></div>")

                f.write('</div></div></div></div></body></html>')
                f.close()
                webbrowser.open('file://' + os.getcwd() + '/' +  filename)
            else:
                logger.warn("Can't open the file {0}. Check your permissions.".format(filename))
