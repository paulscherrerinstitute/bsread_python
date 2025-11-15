import json

import zmq


def zmq_rpc(address, request):
    ctx = zmq.Context()
    sock = zmq.Socket(ctx, zmq.REQ)
    sock.connect(address)

    # Normal strings indicate that the request is already JSON encoded
    if isinstance(request, str):
        sock.send_string(request)
    else:
        sock.send_string(json.dumps(request))

    response = sock.recv_json()

    sock.close()
    ctx.destroy()

    return response



