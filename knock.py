'''A script that serves an HTTP page on a configurable URL and executes a predefined command
if the user submits the correct password. The password is never sent on the network by the
web app, only a MD5 hash salted with a long random string.

It has no dependencies other than the batteries included in Python. The HTML part of the app
loads JQuery and crypto-js/md5 from a CDN.

The script can be used to execute firewall rules in order to open up some ports for the calling IP.

It is called knock.py because it is similar to port knocking except that a password is used.

Sample config file
==================
    [config]
    port = 8080            => port on which the server should listen
    path = foo             => the URL on which the web app is served (ideally, should be hard to guess)
    password = secret      => the secret password (ideally, should be impossible to guess)
    command = echo "Successful connection from %IP"     
                           => the command to launch on server when the client submits the correct password
'''
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import urlparse, cgi, os, sys, binascii, hashlib, ConfigParser

CONFIG = {}
CACHE = {}
INDEX = '''<script src="http://crypto-js.googlecode.com/svn/tags/3.1.2/build/rollups/md5.js"></script>
<script src="http://cdnjs.cloudflare.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>
<script>
$(function() {
  function submit() { $("#pw").val(CryptoJS.MD5($("#pass").val() + "CHALLENGE")); }
  $("form").submit(submit);
  $("#pass").change(submit);
});
</script>
<input type="password" id="pass">
<form method="post"><input type="hidden" name="pw" id="pw"/><input type="submit"/></form>
'''
def md5(s):
    h = hashlib.md5()
    h.update(s)
    return h.hexdigest()

class GetHandler(BaseHTTPRequestHandler):
    def reply(self, response, headers=None):
        '''Helper method for sending a string response back, with optional headers.'''
        self.send_response(200)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(response)

    def index(self):
        '''Bootstraps the "web app" when the secret URL is called.'''
        chal = CACHE[self.client_address[0]] = binascii.b2a_hex(os.urandom(25))
        self.reply(INDEX.replace('CHALLENGE', chal), {'Content-Type': 'text/html'})

    def knock(self):
        '''Verifies the challenge submitted by the user.'''
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, 
                                environ={'REQUEST_METHOD':'POST', 'CONTENT_TYPE':self.headers['Content-Type'], }) 
        if form['pw'].value == md5(CONFIG['password'] + CACHE.pop(self.client_address[0])):
            self.reply(CONFIG.get('welcome', 'Welcome!'))
            os.system(CONFIG['command'].replace('%IP', self.client_address[0]))
        
    def check_path(self):
        '''Checks that the URL is valid (otherwise no response will be sent).'''
        return self.path.strip('/') == CONFIG.get('path', '')

    def do_POST(self):
        if self.check_path(): 
            return self.knock()
        
    def do_GET(self):
        if self.check_path():
            return self.index()

if __name__ == '__main__':
    cfg = ConfigParser.ConfigParser()
    cfg.read((sys.argv + ['knock.cfg'])[1:2])
    CONFIG.update(dict(cfg.items('config')))
    HTTPServer(('0.0.0.0', int(CONFIG.get('port', 8080))), GetHandler).serve_forever()
