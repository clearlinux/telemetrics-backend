## Plugable payload parsers

### Overview

A plugable parser is a python module that encapsulates a data transformation.
This transformation is applied to telemetry message payload if the classification
matches one of the classifications that the parser defines during plugin
registration.

Plugin registration occurs during collector initialization, to enable a plugin
the plugin needs to be listed in the array ```POST_PROCESSING_PARSERS``` in
collector configuration.

For example to enable the ```demo``` parser plugin that comes with the telemetry
backend we need to add a line like the following to collector configuration:

```python

class Config(object):

    # ... some configuration values

    POST_PROCESSING_PARSERS = ["demo"]

    # ... more configuration values

```


### Plugable parser `installation`

The plugable parser module needs to be located under parsers directory, see
the following plugin parser source tree:

```bash
<telemetry-root>/collector/collector/
                                    parsers/
                                            <parser_name_dir>/
                                                            __init__.py
                                                            main.py
```

* ```<parser_name_dir>``` is the parser module name and should live under
collector/parsers
* ```main.py``` is the entry point for plugin registration.

The parser entry point `must have` the following members:

* An array called ```CLASSIFICATIONS``` with a list of message classifications. Any message
that matches one of these classifications will be parsed by this plugin.

* A function signature ```parse_payload(kwargs)```
which is the transformation that will be applied to the payload.

### Other considerations

Plugable parsers are applied asynchronously and no major consideration is required for
most use cases. When in doubt keep in mind the following:

* Payload transformations are applied after the message record (including payload)
is safely stored.
* It is a correct assumption to think that the entire record can
be queried from storage.
* It is not possible to register multiple plugins for the same classification,
the correct way to go about doing this is to encapsulate the multiple
transformations in one plugin. This is by design, remember that transformations
are applied asynchronously therefore a given plugin execution order is not
guaranteed.
