#!/usr/bin/env python3
"""Loopback-only media review with explicit file allowlist and seekable MP4 range responses."""
import argparse,functools,http.server,json,mimetypes,re
from pathlib import Path
ROOT=None
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        self.media_request(True)
    def do_HEAD(self):
        self.media_request(False)
    def media_request(self,include_body):
        if not self.path.startswith('/media/'): return super().do_GET() if include_body else super().do_HEAD()
        files=json.loads((ROOT/'media-map.json').read_text());key=self.path[7:].split('?',1)[0];file=Path(files[key]) if key in files else None
        if file is None or not file.is_file():return self.send_error(404)
        size=file.stat().st_size;lo,hi=0,size-1;rng=self.headers.get('Range');partial=False
        if rng:
            m=re.fullmatch(r'bytes=(\d*)-(\d*)',rng)
            if not m or not (m[1] or m[2]):return self.send_error(416)
            if m[1]:lo=int(m[1]);hi=min(int(m[2]) if m[2] else hi,hi)
            elif m[2]:lo=max(0,size-int(m[2]))
            if lo>hi or lo>=size:return self.send_error(416)
            partial=True
        self.send_response(206 if partial else 200);self.send_header('Content-Type',mimetypes.guess_type(file)[0] or 'application/octet-stream');self.send_header('Content-Length',str(hi-lo+1));self.send_header('Accept-Ranges','bytes')
        if partial:self.send_header('Content-Range',f'bytes {lo}-{hi}/{size}')
        self.end_headers()
        if not include_body:return
        try:
            with file.open('rb') as f:
                f.seek(lo);remaining=hi-lo+1
                while remaining:
                    chunk=f.read(min(1048576,remaining))
                    if not chunk:break
                    self.wfile.write(chunk);remaining-=len(chunk)
        except (BrokenPipeError,ConnectionResetError):pass
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--dir',required=True,type=Path);ap.add_argument('--port',type=int,default=0);a=ap.parse_args();ROOT=a.dir.resolve();assert (ROOT/'media-map.json').is_file()
    server=http.server.ThreadingHTTPServer(('127.0.0.1',a.port),functools.partial(Handler,directory=str(ROOT)))
    print(f'http://127.0.0.1:{server.server_port}/',flush=True);server.serve_forever()
