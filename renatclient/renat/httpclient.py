import urllib
import StringIO
import httplib
import os
import urlparse

from twisted.internet import reactor
from twisted.web.http_headers import Headers
from twisted.web.error import Error
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.web.client import Agent, readBody, FileBodyProducer, ProxyAgent, BrowserLikeRedirectAgent
from twisted.python.failure import Failure

GET = "GET"
POST = "POST"

def request(method, url, values={}, header={}, return_headers=False, pool=None, proxy=None):
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
    
    :param proxy: URL to the proxy. An empty string or no proxy. `None` to check
      the environment variable `http_proxy`.
    """
    
    if method != GET and method != POST:
        raise ValueError("Unsupported method")
    
    agent = _make_agent(pool, proxy)
    
    values = urllib.urlencode(values)
    if values:
        if method == GET:
            url = url + "?" + values
            request_body = None
        else:
            request_body = FileBodyProducer(StringIO.StringIO(values))
    else:
        request_body = None
    
    def got_response(response):
        
        def got_body(response_body):
            if return_headers:
                response_headers = dict(response.headers.getAllRawHeaders())
                return (response_body, response_headers)
            else:
                return response_body

        if response.code != httplib.OK:
            return Failure(Error(response.code))
        d = readBody(response)
        d.addCallback(got_body)
        return d
    
    d = agent.request(
        method,
        url,
        Headers(header),
        request_body)
    
    d.addCallback(got_response)
    return d


def _make_agent(pool=None, proxy=None):
    proxy_host, proxy_port = _get_proxy(proxy) 
    if proxy_host:
        endpoint = TCP4ClientEndpoint(reactor, proxy_host, proxy_port)
        agent = ProxyAgent(endpoint, pool=pool)
    else:
        agent = Agent(reactor, pool=pool)
    agent = BrowserLikeRedirectAgent(agent)
    return agent


def _get_proxy(proxy=None):
    """
    Returns `(hostname, port)` of proxy, or `(None, None)` if no proxy is to be used.
    """
    if proxy is None:
        proxy = os.environ.get("http_proxy", "")
    if proxy:
        parts = urlparse.urlparse(proxy)
        if parts.scheme != "http":
            raise ValueError("Proxy protocol %s is not supported" % repr(parts.scheme))
        hostname = parts.hostname
        port = parts.port
        if not port:
            port = 80
        if hostname:
            return (hostname, port)
        else:
            return (None, None)
    else:
        return (None, None)