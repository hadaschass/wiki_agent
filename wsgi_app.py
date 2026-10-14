"""Production HTTP entry point for Gunicorn."""
import json
from pathlib import Path

from wiki_agent import ResearchError, TopicAgent, Wikipedia


def application(environ, start_response):
    path, method = environ.get('PATH_INFO', '/'), environ.get('REQUEST_METHOD', 'GET')
    status, content_type = '200 OK', 'application/json; charset=utf-8'
    trace = []
    if path == '/' and method == 'GET':
        body = Path(__file__).with_name('index.html').read_bytes()
        content_type = 'text/html; charset=utf-8'
    elif path == '/api/explain' and method == 'POST':
        try:
            length = int(environ.get('CONTENT_LENGTH') or '0')
            if not 0 < length <= 8192:
                raise ValueError('Please submit a topic of up to 500 characters.')
            data = json.loads(environ['wsgi.input'].read(length))
            if not isinstance(data, dict) or not isinstance(data.get('topic'), str):
                raise ValueError('A text topic is required.')
            answer = TopicAgent(Wikipedia(), trace.append).explain(data['topic'])
            result = {'answer': answer, 'trace': trace}
        except (ValueError, UnicodeDecodeError) as exc:
            status, result = '400 Bad Request', {'error': str(exc), 'trace': trace}
        except ResearchError as exc:
            status, result = '502 Bad Gateway', {'error': str(exc), 'trace': trace}
        body = json.dumps(result).encode()
    else:
        status, body = '404 Not Found', b'{"error":"Not found"}'
    start_response(status, [('Content-Type', content_type), ('Content-Length', str(len(body))),
                            ('X-Content-Type-Options', 'nosniff')])
    return [body]
