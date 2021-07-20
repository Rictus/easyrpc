import asyncio
import os, time
import pytest
import subprocess, signal
from easyrpc.proxy import EasyRpcProxy

SERVER = '0.0.0.0'

SERVER_A_PORT = 8320
SERVER_A = 'tests.cluster_a'

SERVER_B_PORT = 8321
SERVER_B = 'tests.cluster_b'

SERVER_C_PORT = 8322
SERVER_C = 'tests.cluster_c'

def server_manager():
    """
    starts uvicorn server for testing, and cleans up once finished
    """
    server_a_p = subprocess.Popen(
        f"uvicorn --host {SERVER} --port {SERVER_A_PORT} {SERVER_A}:server".split(' ')
    )
    time.sleep(10)
    server_b_p = subprocess.Popen(
        f"uvicorn --host {SERVER} --port {SERVER_B_PORT} {SERVER_B}:server".split(' ')
    )
    time.sleep(10)

    server_c_p = subprocess.Popen(
        f"uvicorn --host {SERVER} --port {SERVER_C_PORT} {SERVER_C}:server".split(' ')
    )

    print(f"server_manager - started server_a and server_b")
    yield 'started'
    for p in [server_a_p, server_b_p, server_c_p]:
        p.send_signal(
            signal.SIGTERM
        )
        print(f"pid is {p.pid}")
        p.wait()
    print(f"server_manager - stopped server_a and server_b")

@pytest.fixture
def manager():
    yield from server_manager()

@pytest.mark.asyncio
async def test_cluster_c(manager):
    await asyncio.sleep(10)
    # create basic proxy - call methods
    proxy = await EasyRpcProxy.create(
        SERVER, 
        SERVER_C_PORT, 
        '/ws/cluster', 
        server_secret='abcd1234',
        namespace='shared'
    )
    await asyncio.sleep(20)
    expected = {'data': 'test'}
    result = await proxy['cluster_b_func'](expected)
    assert result == expected, f"expected result of {expected}"

    result = await proxy['cluster_a_func'](expected)
    assert result == expected, f"expected result of {expected}"

    result = await proxy['cluster_c_func'](expected)
    assert result == expected, f"expected result of {expected}"