'''A script that serves an HTTP page on a configurable URL and executes a predefined command
if the user submits the correct password. The password is never sent on the network by the
web app, only a MD5 hash salted with a long random string.

Sample config
    [config]
    password = secret
    path = foo
    command = echo OK
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
        self.send_response(200)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(response)

    def index(self):
        chal = CACHE[self.client_address[0]] = binascii.b2a_hex(os.urandom(25))
        self.reply(INDEX.replace('CHALLENGE', chal), {'Content-Type': 'text/html'})

    def knock(self):
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, 
                                environ={'REQUEST_METHOD':'POST', 'CONTENT_TYPE':self.headers['Content-Type'], }) 
        if form['pw'].value == md5(CONFIG['password'] + CACHE.pop(self.client_address[0])):
            self.reply(CONFIG.get('welcome', 'Welcome!'))
            os.system(CONFIG['command'])
        
    def check_path(self):
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
    HTTPServer(('0.0.0.0', CONFIG.get('port', 8080)), GetHandler).serve_forever()
                                                                                          1,1          Haut

