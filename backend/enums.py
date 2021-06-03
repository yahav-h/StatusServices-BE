from enum import Enum


class AppStates(Enum):
    Success = "Success"
    Pending = "Pending"
    Fail = "Fail"
    Done = "Done"
    ServiceUp = "Up"
    ServiceDown = "Down"


class AppRoutes(Enum):
    Ping = "/api/v1/ping"
    Health = "/api/v1/health"
    Domains = "/api/v1/domains"


