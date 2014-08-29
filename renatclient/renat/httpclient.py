import urllib
import StringIO
import httplib

from twisted.internet import reactor, defer
from twisted.web.http_headers import Headers
from twisted.web.error import Error
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.web.client import Agent, readBody, FileBodyProducer, ProxyAgent, BrowserLikeRedirectAgent
from twisted.python.failure import Failure

GET = "GET"
POST = "POST"

@defer.inlineCallbacks
def request(method, url, values={}, header={}, return_headers=False, pool=None, proxy_host=None, proxy_port=80):
    """
    Performs an HTTP request.
    
    :param method: Either `GET` or `POST`.
    
    :param url: URL to which the request is made.
    
    :param values: Either a dict or a list of tuples with the values
      passed along with the request. For a GET request, they are encoded into the URL,
      for a POST request they are passed in the body of the request.
    
    :param headers: Dict with the header values to send.
    
    :param return_headers: If `True` the function will return a `(body, header)` tuple
      with both the body of the answer and the headers. If `False` the function returns 
      the body only. Defaults to `False`.
      
    :param pool: Optional instance of `HTTPConnectionPool` for keep-alive. Defaults to
      not using a connection pool.
    
    :param proxy_host: Hostname or IP of the proxy to use. Defaults to not using a proxy.
    
    :param proxy_port: Port of the proxy to use. Defaults to 80.
    """
    
    if method != GET and method != POST:
        raise ValueError("Unsupported method")
    
    agent = _make_agent(pool, proxy_host, proxy_port)
    
    values = urllib.urlencode(values)
    if values:
        if method == GET:
            url = url + "?" + urllib.urlencode(values)
            request_body = None
        else:
            request_body = FileBodyProducer(StringIO.StringIO(values))
    else:
        request_body = None
    
    d = agent.request(
        method,
        url,
        Headers(header),
        request_body)

    response = yield d
    
    if response.code != httplib.OK:
        defer.returnValue(Failure(Error(response.code)))
    
    response_body = yield readBody(response)
    
    if return_headers:
        response_headers = dict(response.headers.getAllRawHeaders())
        defer.returnValue((response_body, response_headers))
    else:
        defer.returnValue(response_body)


def _make_agent(pool=None, proxy_host=None, proxy_port=80):
    if proxy_host:
        endpoint = TCP4ClientEndpoint(reactor, proxy_host, proxy_port)
        agent = ProxyAgent(endpoint, pool=pool)
    else:
        agent = Agent(reactor, pool=pool)
    agent = BrowserLikeRedirectAgent(Agent(reactor))
    return agent
        