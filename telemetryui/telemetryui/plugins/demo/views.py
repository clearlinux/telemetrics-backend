
from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

TAB_NAME = "Plugin Demo"

plugin_demo = Blueprint('plugin_demo', __name__,
                        template_folder='templates')


@plugin_demo.route('/demo', methods=['GET'])
def echo():
    message = "this is a view plugin demo"
    return render_template('demo.html', message=message)


@plugin_demo.route('/echo_name/<username>', methods=['GET'])
def echo_name(username):
    try:
        return 'Hello {}'.format(username)
    except TemplateNotFound:
        abort(404)


@plugin_demo.route('/echo_template/<username>', methods=['GET'])
def echo_template(username):
    try:
        return render_template('demo.html', username=username)
    except TemplateNotFound:
        abort(404)


def init(register_fn):
    register_fn(plugin_demo)
