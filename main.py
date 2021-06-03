import subprocess, shlex
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_EXCEPTION
from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from backend.lambdas import Stamp, DateNow
from backend.enums import AppStates, AppRoutes
from backend.datatypes import Tasks
from backend.database import db_session, db_init
from fastapi.middleware.cors import CORSMiddleware
import socket


app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.middleware('http')
async def add_process_time_header(request: Request, call_next):
    start_time = Stamp()
    response: Response = await call_next(request)
    response.headers['x-process-time'] = str(Stamp() - start_time)
    return response


@app.get(path=AppRoutes.Health.value)
def health():
    content = {
        'status': AppStates.Success.value,
        'timestamp': DateNow()
    }
    json = jsonable_encoder(obj=content)
    return JSONResponse(content=json, status_code=200)


async def ping_domain(address):
    def ping(address):
        cmd = f'ping -c 4 {address}'
        args = shlex.split(cmd)
        try:
            proc = subprocess.Popen(args, stdout=subprocess.PIPE)
            proc.wait(10)
            if proc.poll():
                return False, proc.stdout.read()
            else:
                return True, proc.stdout.read()
        except Exception as e:
            print(e)
            return False, None
    try:
        with ThreadPoolExecutor(max_workers=1, thread_name_prefix=f'PING_{address}') as executor:
            future = executor.submit(ping, address)
            state = wait(fs=[future], timeout=120, return_when=FIRST_EXCEPTION)
            if state.done:
                result = state.done.pop()
            if result._state == 'Finished':
                future.set_result(result._state)
            obj = future.result()
            return obj
    except:
        return False


@app.post(path=AppRoutes.Ping.value)
async def task_ping(request: Request):
    identifier = request.query_params.get('identifier')
    if not identifier:
        content = {
            'status': AppStates.Fail.value,
            'timestamp': DateNow(),
        }
        json = jsonable_encoder(obj=content)
        return JSONResponse(content=json, status_code=400)

    service_id, service_name = tuple(identifier.split(":", 1))
    try:
        ip = socket.gethostbyname(service_name.split("://")[-1])
    except:
        ip = service_name.split("://")[-1]
    task_obj = Tasks.query.filter_by(taskID=service_id, serviceName=service_name, serviceIP=ip).first()
    if not task_obj:
        task_obj = Tasks(taskID=service_id, serviceName=service_name, serviceIP=ip, taskStatus=AppStates.Pending.value)

    result = await ping_domain(ip)
    if not result[0]:
        task_obj.serviceStatus = AppStates.ServiceDown.value
    else:
        task_obj.serviceStatus = AppStates.ServiceUp.value
        task_obj.lastTimeCheck = DateNow()
    task_obj.taskStatus = AppStates.Done.value
    task_id = task_obj.taskID

    db_session.add(task_obj)
    db_session.commit()

    content = {
        'status': AppStates.Success.value,
        'timestamp': DateNow(),
        'taskID': task_id
    }
    json = jsonable_encoder(obj=content)
    return JSONResponse(content=json, status_code=200)


@app.get(path=AppRoutes.Domains.value)
async def fetch_domains():
    records = Tasks.query.all()
    if not records:
        content = {
            'status': AppStates.Success.value,
            'timestamp': DateNow(),
            'domains': []
        }
        json = jsonable_encoder(obj=content)
        return JSONResponse(content=json, status_code=200)
    list_of_records = []
    for record in records:
        result = await ping_domain(record.serviceIP)
        if not result[0]:
            record.serviceStatus = AppStates.ServiceDown.value
        else:
            record.serviceStatus = AppStates.ServiceUp.value
            record.lastTimeCheck = DateNow()
        obj = {
            'taskId': record.taskID,
            'serviceName': record.serviceName,
            'serviceIP': record.serviceIP,
            'serviceStatus': record.serviceStatus,
            'taskStatus': record.taskStatus,
            'timeCreated': record.timeCreated,
            'lastTimeCheck': record.lastTimeCheck
        }
        list_of_records.append(obj)
        db_session.add(record)
        db_session.commit()
    content = {
        'status': AppStates.Success.value,
        'timestamp': DateNow(),
        'domains': list_of_records
    }
    json = jsonable_encoder(obj=content)
    return JSONResponse(content=json, status_code=200)


@app.delete(path=AppRoutes.Domains.value)
async def remove_task(request: Request):
    identifier = request.query_params.get('identifier')
    if not identifier:
        content = {
            'status': AppStates.Fail.value,
            'timestamp': DateNow(),
        }
        json = jsonable_encoder(obj=content)
        return JSONResponse(content=json, status_code=400)
    service_id, service_name = tuple(identifier.split(":", 1))
    task_obj = Tasks.query.filter_by(taskID=service_id, serviceName=service_name).first()
    if not task_obj:
        content = {
            'status': AppStates.Success.value,
            'timestamp': DateNow(),
        }
        json = jsonable_encoder(obj=content)
        return JSONResponse(content=json, status_code=404)
    db_session.delete(task_obj)
    db_session.commit()
    content = {
        'status': AppStates.Success.value,
        'timestamp': DateNow()
    }
    json = jsonable_encoder(obj=content)
    return JSONResponse(content=json, status_code=200)

if __name__ == '__main__':
    from sys import exit
    import uvicorn
    if not db_init():
        exit()
    else:
        uvicorn.run('main:app', host="0.0.0.0", port=53459)
