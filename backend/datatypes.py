from sqlalchemy.sql.util import Column
from sqlalchemy.types import Text
from backend.database import Base
from backend.lambdas import DateNow


class Tasks(Base):
    __tablename__ = "tasks_tbl"
    taskID = Column(Text(), primary_key=True, unique=True, nullable=False, autoincrement=False)
    serviceName = Column(Text(), unique=False, nullable=False)
    serviceIP = Column(Text(), unique=False, nullable=True, default="N/a")
    taskStatus = Column(Text(), unique=False, nullable=False)
    serviceStatus = Column(Text(), unique=False, nullable=True)
    timeCreated = Column(Text(), unique=False, nullable=False)
    lastTimeCheck = Column(Text(), unique=False, nullable=True)

    def __init__(self,
                 taskID=None,
                 serviceName=None,
                 serviceIP=None,
                 taskStatus=None,
                 lastTimeCheck=None
                 ):
        self.taskID = taskID
        self.serviceName = serviceName
        self.serviceIP = serviceIP
        self.taskStatus = taskStatus
        self.timeCreated = DateNow()
        self.lastTimeCheck = DateNow(epoch=True) if not lastTimeCheck else lastTimeCheck

    def __repr__(self):
        return "<Task %s, %s>" % self.taskID, self.taskStatus
