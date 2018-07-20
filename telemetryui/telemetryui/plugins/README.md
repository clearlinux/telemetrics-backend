## telemetrics-backend view plugins

### Overview

View plugins is a way to extend the available views in the telemetryui
without modifying code in the core of the application. This is important
because custom modifications to the core could make difficult for users
to update their deployment with new releases.

Plugins provide a reasonable encapsulation/separation of the plugin logic
and still allows the plugins to access core component i.e. base.html template.


### Plugin encapsulated

Plugin code should be in a folder with a descriptive name and it should be an acceptable
[PEP8 module name](https://www.python.org/dev/peps/pep-0008/#package-and-module-names).
Telemetryui view plugins are essentially [flask blueprints](http://flask.pocoo.org/docs/0.12/blueprints/)
therefore a plugin can define its own resource folders (templates and static) that live
in the same folder as the rest of the plugin code (i.e.)

```bash
plugin_root/
        views.py
        helpers.py
        templates/
                main.html
                snipet.html
        static/
              main.css
              main.js
```

Note that plugins are able to access templates declared at the app level. The flask templating
system will try to find a template initially in the list of templates registered by the main app. 


### Where to "install" plugins 

"Encapsulated" plugins go under the plugins folder under telemeryui sub folder.

```bash

<telemetryui-root>/telemetryui/telemetryui/
                                          static/
                                          templates/
                                          plugins/
                                          model.py
                                          config.py
                                          updates.py
                                          ....
```

Notice in the core folder structure there is a static and templates folder. Plugins (blueprints)
can have their own templates and static folder.    


### Attributes required in a plugin view

Plugins are expected to have a views.py file with all the views that the plugin
provides (i.e.)

```bash
plugin_root/
            __init__.py
            views.py
            templates
```

Plugins are imported as python modules, therefore  ```__init__.py``` is required.

views.py must have a variable with the name TAB_NAME, this is the name of the
tab that will be displayed on the telemetryui (i.e.)

```python
import os
...

TAB_NAME = "My Plugin"

...
```

views.py must have an init function with the following syntax:

```python

from flask import Blueprint

my_plugin = Blueprint('my_plugin', __name__)

...

def init(fn):
    fn(my_plugin)

```

The init function is used to pass the blueprint to the core for registration.


### Installing plugins

To "install" a plugin into telemetryui copy the plugin folder to the plugins
folder under telemetryui (i.e.)

```bash

cp my_plugin  my_plugin
```

un-comment the PLUGINS section of config (or config_local) and add your plugin to
the list (i.e.). 

```bash

class Config(object):
    DEBUG = True
    TESTING = False
    LOG_LEVEL = logging.ERROR
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres:postgres@localhost/telemetry'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    LOG_FILE = 'telemetryui.log'
    WTF_CSRF_ENABLED = True
    SECRET_KEY = 'a secret key'

    # Uncomment next line 
    PLUGINS = ['my_plugin']
```

Remember the plugin name is the name of the python module that was dropped
in the plugins folder in telemetryui.


### Considerations when multiple plugins are installed

Because plugins are flask blueprints the same considerations should be applied when
multiple plugins are added.

When specifying a *template directory* (see following code snippet)

```python
my_plugin = Blueprint('my_plugin', __name__, template_folder="template")
```

Make sure that there is no templates with the same name on other plugins otherwise the
app will used the template file that was registered first. For example if we have pluginview_2
and pluginview_2 and both have a relative template directory and both have a view_template.html
the plugins that is registered first (the first plugin in the list of plugins in configuration file).
A good rule is to name templates prepending the name of the plugin to the template. i.e.

```buildoutcfg
plugins/
        pluginview_1/
                    __init__.py
                    views.py
                    templates/
                            pluginview_1_index.html

        pluginview_2/
                    __init__.py
                    views.py
                    templates/
                            pluginview_2_index.html

```

For more advanced uses like overwriting templates (not recommended) read [this](http://flask.pocoo.org/docs/0.12/blueprints/#templates) section on flask blueprints.


For *static content* the behavior can be controlled with **static_folder** and **static_url_path** blueprint parameters for
example for:

```buildoutcfg
plugins/
        my_plugin/
                  __init__.py
                  views.py
                  templates
                  static/
                        my_plugin.css

        your_plugin/
                    __init__.py
                    views.py
                    templates
                    static/
                          your_plugin.css

```

And:

**plugins/my_plugin/views.py**
```python
my_plugin = Blueprint('my_plugin', __name__,
                      template_folder="template",
                      static_url_path="/my_plugin/static",
                      static_folder="static")
```

**plugins/your_plugin/views.py**
```python
your_plugin = Blueprint('your_plugin', __name__,
                        template_folder="template",
                        static_url_path="/your_plugin/static",
                        static_folder="static")
```

The location of the static files will be:

```commandline
/telemetryui/plugins/my_plugin/static/css/my_plugin.css
/telemetryui/plugins/your_plugin/static/css/your_plugin.css
```

Specifying the static_url_path allows flask to resolve the link to the right
file if two plugins have static files with the same name and extension.  

### utility functions for creating views

The demo example in the plugins folder makes use of utility functions to simplify
the creation of a plugin.

```python
from telemetryui.plugins.telem_view import (
    new_telem_view,
    get_default_route,)
``` 

These two imported functions can be used to create the blueprint and obtain the default route
for the tab created by the plugin.

```python

# new_telem_view: Creates and returns a blueprint with the import name as parameter, all
# the details about the blueprint creation are abstracted behind this function

plugin_demo = new_telem_view(__name__)
```

For the default route for the plugin we can use:

```python

# get_default_route: extracts plugin name from the import name and returns the route
# path for this plugin

@plugin_demo.route(get_default_route(__name__), methods=['GET'])

```

