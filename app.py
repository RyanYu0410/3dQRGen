from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
import json,secrets,threading,subprocess,webbrowser,uuid,os
from model import generate
ROOT=Path(__file__).resolve().parent;OUTPUT=ROOT/'generated';TOKEN=secrets.token_urlsafe(24);LOCK=threading.Lock();JOBS={};PORT=int(os.environ.get('QR_MAKER_PORT','8765'));ORIGIN=f'http://127.0.0.1:{PORT}'
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def reply(self,status,data,kind='application/json'):
  raw=json.dumps(data).encode() if kind=='application/json' else data
  self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  if self.headers.get('Host') not in (f'127.0.0.1:{PORT}',f'localhost:{PORT}'):return self.reply(403,{'error':'Local requests only'})
  path=urlsplit(self.path).path
  if path=='/':return self.reply(200,(ROOT/'index.html').read_text().replace('__TOKEN__',TOKEN).encode(),'text/html; charset=utf-8')
  if path.startswith('/file/'):
   bits=path.split('/')
   if len(bits)!=4 or bits[2] not in JOBS or bits[3] not in ['qr.png','QR_project.3mf','QR_single_color.stl','base.stl','qr_pattern.stl','PRINT_README.txt']:return self.reply(404,{'error':'Not found'})
   p=OUTPUT/bits[2]/bits[3];return self.reply(200,p.read_bytes(),'image/png' if p.suffix=='.png' else 'application/octet-stream')
  return self.reply(404,{'error':'Not found'})
 def do_POST(self):
  if self.headers.get('X-QR-Token')!=TOKEN or self.headers.get('Origin') not in (ORIGIN,None):return self.reply(403,{'error':'Open the local app to continue.'})
  try:
   length=int(self.headers.get('Content-Length','0'))
   if length>4096:raise ValueError('Request too large')
   data=json.loads(self.rfile.read(length))
   if self.path=='/generate':
    if not LOCK.acquire(False):return self.reply(409,{'error':'A model is already generating.'})
    try:
     ident=uuid.uuid4().hex;meta=generate(OUTPUT/ident,data.get('url',''),data.get('diameter',35),bool(data.get('grip',True)),data.get('style','hollow'));JOBS[ident]=meta
    finally:LOCK.release()
    return self.reply(200,dict(id=ident,**meta))
   if self.path=='/studio':
    ident=data.get('id')
    if ident not in JOBS:raise ValueError('Generate a model first.')
    app=Path('/Applications/BambuStudio.app')
    if not app.exists():raise ValueError('Install Bambu Studio first.')
    subprocess.run(['open','-a',str(app),str(OUTPUT/ident/'QR_project.3mf')],check=True)
    return self.reply(200,{'message':'Opened Bambu Studio. Select A1 and your filament, check color assignments, Slice plate, then Print plate. Choose your connected A1. Nothing has been sent or started automatically.'})
   return self.reply(404,{'error':'Not found'})
  except (ValueError,KeyError,json.JSONDecodeError) as e:self.reply(400,{'error':str(e)})
  except Exception as e:self.reply(500,{'error':'Operation failed: '+str(e)})
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',PORT),Handler)
 if os.environ.get('QR_MAKER_NO_BROWSER')!='1':webbrowser.open(ORIGIN)
 print('QR Maker running at '+ORIGIN,flush=True);server.serve_forever()
