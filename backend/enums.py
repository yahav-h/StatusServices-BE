from enum import Enum


class AppState(Enum):
    Success = "Success"
    Pending = "Pending"
    Fail = "Fail"


class AppRoutes(Enum):
    Ping = "/api/v1/ping"
    Root = "/"


