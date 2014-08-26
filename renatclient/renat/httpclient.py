import urllib
import StringIO

from twisted.internet import reactor, defer
from twisted.web.http_headers import Headers
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.web.client import Agent, readBody, FileBodyProducer, ProxyAgent


@defer.inlineCallbacks
def get(url, values={}, header={}, pool=None, proxy_host=None, proxy_port=80):
    
    agent = _make_agent(pool, proxy_host, proxy_port)
    if values:
        url = url + "?" + urllib.urlencode(values)
    
    d = agent.request(
        'GET',
        url,
        Headers(header),
        None)

    response = yield d
    response_body = yield readBody(response)
    defer.returnValue((response, response_body))
    
    
@defer.inlineCallbacks
def post(url, values={}, header={}, pool=None, proxy_host=None, proxy_port=80):
    
    agent = _make_agent(pool, proxy_host, proxy_port)
    request_body = FileBodyProducer(StringIO.StringIO(urllib.urlencode(values)))
        
    d = agent.request(
        'POST',
        url,
        Headers(header),
        request_body)

    response = yield d
    response_body = yield readBody(response)
    defer.returnValue((response, response_body))
    
    
def _make_agent(pool=None, proxy_host=None, proxy_port=80):
    if proxy_host:
        endpoint = TCP4ClientEndpoint(reactor, proxy_host, proxy_port)
        agent = ProxyAgent(endpoint, pool=pool)
    else:
        agent = Agent(reactor, pool=pool)
    return agent
        