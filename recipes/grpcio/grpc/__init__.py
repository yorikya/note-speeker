print("Dummy grpc package loaded")

class StatusCode:
    OK = 0
    CANCELLED = 1
    UNKNOWN = 2
    INVALID_ARGUMENT = 3
    DEADLINE_EXCEEDED = 4
    NOT_FOUND = 5
    ALREADY_EXISTS = 6
    PERMISSION_DENIED = 7
    RESOURCE_EXHAUSTED = 8
    FAILED_PRECONDITION = 9
    ABORTED = 10
    OUT_OF_RANGE = 11
    UNIMPLEMENTED = 12
    INTERNAL = 13
    UNAVAILABLE = 14
    DATA_LOSS = 15
    UNAUTHENTICATED = 16

class RpcError(Exception):
    pass

class AioRpcError(Exception):
    pass

class FutureTimeoutError(Exception):
    pass

class UnaryUnaryClientInterceptor:
    pass

import sys
sys.modules['grpc'].StatusCode = StatusCode
sys.modules['grpc'].RpcError = RpcError
sys.modules['grpc'].AioRpcError = AioRpcError
sys.modules['grpc'].FutureTimeoutError = FutureTimeoutError
sys.modules['grpc'].UnaryUnaryClientInterceptor = UnaryUnaryClientInterceptor 