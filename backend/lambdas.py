from time import time
from datetime import datetime


DateNow = lambda epoch=False: datetime.now().isoformat() if not epoch else datetime(1970, 1, 1).isoformat()
Stamp = lambda: time()
