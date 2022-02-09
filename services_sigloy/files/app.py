from os import path

from aiofiles.os import stat as aio_stat
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette import status

file_router = APIRouter(
    prefix="/files",
    tags=["Files handler"],
    dependencies=[])

"""Static files is handled of "StaticFiles" module in main.py line 54"""


@file_router.get('/get/{file_id}')
async def get_private_file(file_id: str):
    # TODO (PHASE 2) check accessibility of the user and raise forbidden
    file_path = path.join('storage', 'private', file_id)
    try:
        # check file exists or not
        await aio_stat(file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return FileResponse(file_path)


"""Mongo storage routes(not needed for now)"""
# @file_router.post("/upload")
# async def upload_file(file: UploadFile = File(...)):
#     fid = await MongoStorage.save_file(file)
#     return {"file_id": fid}
#
#
# @file_router.get("/download/{file_id}")
# async def upload_file(file_id: str):
#     file = await MongoStorage.get_file(file_id)
#     return StreamingResponse(file, media_type=file.metadata['content_type'])
