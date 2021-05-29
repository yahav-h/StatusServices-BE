from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from backend.lambdas import Stamp, DateNow
from backend.enums import AppState, AppRoutes
from backend.datatypes import Tasks
from uuid import uuid5, NAMESPACE_URL


app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware('http')
async def add_process_time_header(request: Request, call_next):
    start_time = Stamp()
    response: Response = await call_next(request)
    response.headers['x-process-time'] = str(Stamp() - start_time)
    return response


@app.get(path=AppRoutes.Root.value)
def root():
    try:
        content = {
            'status': AppState.Success.value,
            'timestamp': DateNow()
        }
        json = jsonable_encoder(obj=content)
        return JSONResponse(content=json, status_code=200)
    except Exception as e:
        content = {
            'status': AppState.Fail.value,
            'timestamp': DateNow()
        }
        json = jsonable_encoder(obj=content)
        return JSONResponse(content=json, status_code=400)


@app.get(path=AppRoutes.Ping.value)
def task_ping(request: Request):
    service_ip = request.query_params.get('ip')
    try:
        taskId = uuid5(NAMESPACE_URL, f'{Stamp()}').hex
        content = {
            'status': AppState.Success.value,
            'timestamp': DateNow(),
            service_ip: AppState.Pending.value,
            'taskID': taskId
        }
        json = jsonable_encoder(obj=content)
        return JSONResponse(content=json, status_code=200)
    except Exception as e:
        content = {
            'status': AppState.Fail.value,
            'timestamp': DateNow()
        }
        json = jsonable_encoder(obj=content)
        return JSONResponse(content=json, status_code=400)


@app.get(path=AppRoutes.Ping.value)
def task_status(request: Request):
    try:
        task_id = request.query_params.get('taskid')
        if not task_id:
            content = {
                'status': AppState.Fail.value,
                'timestamp': DateNow(),
                'message': 'Missing task id'
            }
            json = jsonable_encoder(obj=content)
            return JSONResponse(content=json, status_code=400)

        task_obj = Tasks.query.filter_by(id=task_id).first()
        content = {
            task_id: task_ping.service_ip,
            'status': AppState.Success.value,
            'timestamp': DateNow()
        }
        json = jsonable_encoder(obj=content)
        return JSONResponse(content=json, status_code=400)

    except Exception as e:
        content = {
            'status': AppState.Fail.value,
            'timestamp': DateNow()
        }
        json = jsonable_encoder(obj=content)
        return JSONResponse(content=json, status_code=400)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app:app', host="0.0.0.0", port=53459)
