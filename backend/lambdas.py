from time import time
from datetime import datetime
from uuid import uuid5, NAMESPACE_URL


DateNow = lambda epoch=False: datetime.now().isoformat() if not epoch else datetime(1970, 1, 1).isoformat()
Stamp = lambda: time()
MakeTaskID = lambda: uuid5(NAMESPACE_URL, DateNow()).hex
