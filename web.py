import os

import requests
from flask import Flask, request, abort, redirect

app = Flask(__name__)
REMOTE_BASE = os.environ["REMOTE_BASE"]
INITIAL_REDIRECT = os.environ["INITIAL_REDIRECT"]
HOST_HEADERS = [
    'Authorization',
    'Host',
    'X-Forwarded-For',
    'X-Forwarded-Port',
    'X-Forwarded-Proto',
    'X-Forwarded-Protocol',
    'X-Heroku-Dynos-In-Use',
    'X-Heroku-Queue-Depth',
    'X-Heroku-Queue-Wait-Time',
    'X-Real-Ip',
    'X-Request-Start',
    'X-Varnish',
]


@app.route('/favicon.ico', methods=['GET'])
def favicon():
    abort(404)


@app.route('/', methods=['OPTIONS', 'GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
def initial_redirect():
    return redirect(INITIAL_REDIRECT)


@app.route('/<path:path>', methods=['OPTIONS', 'GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
def proxy(path):
    if path.endswith(".css") or path.endswith(".js"):
        abort(404)

    remote_url = f"{REMOTE_BASE}/{path}"
    print(remote_url)
    response = requests.request(request.method, remote_url,
        data=request.data or request.form,
        headers=prepare_headers(request.headers),
        stream=True,
    )
    content = response.raw.read() or response.content
    print(response.status_code)
    print(response.headers)
    print(content)

    if 'Transfer-Encoding' in response.headers and \
       response.headers['Transfer-Encoding'].lower() == 'chunked':
        # WSGI doesn't handle chunked encodings
        del response.headers['Transfer-Encoding']
    if 'Connection' in response.headers and \
       response.headers['Connection'].lower() == 'keep-alive':
        # WSGI doesn't handle keep-alive
        del response.headers['Connection']

    return app.make_response((
        content,
        response.status_code,
        response.headers.items(),
    ))


def prepare_headers(headers):
    # Make sure we have a mutable dictionary
    headers = dict(headers)

    # These are specific to the host environment and shouldn't be forwarded
    for header in HOST_HEADERS:
        if header in headers:
            del headers[header]

    # These are invalid if using the empty defaults
    if 'Content-Length' in headers and headers['Content-Length'] == '':
        del headers['Content-Length']
    if 'Content-Type' in headers and headers['Content-Type'] == '':
        del headers['Content-Type']

    return headers


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
