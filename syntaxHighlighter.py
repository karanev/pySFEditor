from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
import time

class MyHTMLParser(HTMLParser):
    def __init__(self, textpad):
        HTMLParser.__init__(self)
        self.textpad = textpad
    
    def handle_starttag(self, tag, attrs):
        if tag is "span":
            text = self.get_starttag_text()
            _, tktag = attrs
            self.textpad.insert("end", text, tktag)
    
    def handle_data(self, data):
        self.textpad.insert("end", data)
    
    def handle_entityref(self, name):
        c = unichr(name2codepoint[name])
        self.textpad.insert("end", c)

class Highlighter():
    def __init__(self, textpad):
        self.textpad = textpad
        self.parser = MyHTMLParser(self.textpad)
        self.highlight()
    
    def highlight(self):
        print "Hello"###
        self.code = self.textpad.get("1.0", "end-1c")
        self.textpad.delete("1.0", "end")
        for line in highlight(self.code, PythonLexer(), HtmlFormatter()).split("\n"):
            self.parser.feed(line)
        self.textpad.after(10000, self.highlight)
