from common.core import register_plugin
from common.core import AbstractPlugin
import webbrowser


@register_plugin
class RunBrowserPlugin(AbstractPlugin):

    def should_run(self):
        return 'run_browser' in self.item_options and self.item_options['run_browser']

    def check(self):
        webbrowser.open(self.url)
        return True
