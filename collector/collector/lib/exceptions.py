

class PlugablePayloadParserException(Exception):

    def __init__(self, message):
        self.__str__ = message
