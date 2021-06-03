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


app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)


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
    service_ip = request.query_params.get('ip')
    if not service_ip:
        content = {
            'status': AppStates.Fail.value,
            'timestamp': DateNow(),
        }
        json = jsonable_encoder(obj=content)
        return JSONResponse(content=json, status_code=400)

    task_id = MakeTaskID()
    task_obj = Tasks(taskID=task_id, serviceIP=service_ip, taskStatus=AppStates.Pending.value)

    BooleanOrTuple = await ping_domain(service_ip)
    if isinstance(BooleanOrTuple, bool):
        task_obj.serviceStatus = AppStates.ServiceDown.value
    elif isinstance(BooleanOrTuple, tuple):
        task_obj.serviceStatus = AppStates.ServiceUp.value
        task_obj.lastTimeCheck = DateNow()
    task_obj.taskStatus = AppStates.Done.value

    db_session.add(task_obj)
    db_session.commit()

    content = {
        'status': AppStates.Success.value,
        'timestamp': DateNow(),
        'taskID': task_id
    }
    json = jsonable_encoder(obj=content)
    return JSONResponse(content=json, status_code=200)


@app.get(path=AppRoutes.Ping.value)
def task_status(request: Request):
    task_id = request.query_params.get('taskid')
    if not task_id:
        content = {
            'status': AppStates.Fail.value,
            'timestamp': DateNow(),
            'message': 'Missing task id'
        }
        json = jsonable_encoder(obj=content)
        return JSONResponse(content=json, status_code=400)
    task_obj = Tasks.query.filter_by(taskID=task_id).first()
    if not task_obj:
        content = {
            'status': AppStates.Fail.value,
            'timestamp': DateNow(),
            'message': f'Task id \'{task_id}\' does not exists'
        }
        json = jsonable_encoder(obj=content)
        return JSONResponse(content=json, status_code=404)

    service_ip = task_obj.serviceIP
    service_status = task_obj.serviceStatus
    last_time_checked = task_obj.lastTimeCheck
    db_session.add(task_obj)
    db_session.commit()

    content = {
        'status': service_status,
        'timestamp': DateNow(),
        'service': service_ip,
        'serviceTimeCheck': last_time_checked
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
