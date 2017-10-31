
from telemetryui.plugins.telem_view import (
    new_telem_view,
    get_default_route,)
from flask import (
    Blueprint,
    render_template,
    abort,)


TAB_NAME = "Plugin Demo"

plugin_demo = new_telem_view(__name__)


@plugin_demo.route(get_default_route(__name__), methods=['GET'])
def echo():
    message = "this is a view plugin demo"
    return render_template('demo.html', message=message)


def init(register_fn):
    register_fn(plugin_demo)
