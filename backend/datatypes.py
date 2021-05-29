from sqlalchemy.sql.util import Column
from sqlalchemy.types import Text, DateTime
from backend.database import Base
from backend.lambdas import DateNow


class Tasks(Base):
    __tablename__ = "tasks_tbl"
    taskID = Column(Text(), primary_key=True, unique=True, nullable=False, autoincrement=False)
    serviceIP = Column(Text(), unique=False, nullable=False)
    taskStatus = Column(Text(), unique=False, nullable=False)
    timeCreated = Column(DateTime(), unique=False, nullable=False)
    lastTimeCheck = Column(DateTime(), unique=False, nullable=True)

    def __init__(self,
                 taskID=None,
                 serviceIP=None,
                 taskStatus=None
                 ):
        self.taskID = taskID
        self.serviceIP = serviceIP
        self.taskStatus = taskStatus
        self.timeCreated = DateNow()
        self.lastTimeCheck = None

    def __repr__(self):
        return "<Task %s, %s>" % self.taskID, self.taskStatus
