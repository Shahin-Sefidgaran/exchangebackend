import os

import aiofiles
from aiofiles import os as aiofileos
from bson import ObjectId
from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from common.utils import unique_string_gen
from db.mongo.engine import client
# we save file on mongo db for better and easier performance
from logger.loggers import FILES_LOGGER
from logger.tasks import write_log

db = client.files  # create or get files db
fs = AsyncIOMotorGridFSBucket(db)


class MongoStorage:
    @staticmethod
    async def save_file(upload_file: UploadFile) -> str:
        """
        Save the file to the mongo db.
        params:
            file: file-like object
        return:
            returns id of the first inside mongodb
        """
        file_id = await fs.upload_from_stream(
            upload_file.filename,
            upload_file.file,
            metadata={'content_type': upload_file.content_type})
        write_log(FILES_LOGGER, 'debug', 'mongo file handler',
                  f'saving file with id: {file_id} and name: {upload_file.filename}')
        return str(file_id)

    @staticmethod
    async def get_file(file_id: str):
        """
        Gets the from with specified file_id from mongo and streams it out.
        Throw no file exception
        params:
            file_id: id of the file in the mongo
        return:
            returns file stream
        """
        write_log(FILES_LOGGER, 'debug', 'mongo file handler', f'Accessing file with id: {file_id}')
        fid = ObjectId(file_id)
        grid_out = await fs.open_download_stream(fid)
        return grid_out

    @staticmethod
    async def delete_file(file_id) -> None:
        """Get _id of file to delete"""
        write_log(FILES_LOGGER, 'debug', 'mongo file handler', f'Deleting file with id: {file_id}')
        await fs.delete(file_id)

    @staticmethod
    async def delete_all_files() -> None:
        """Get _id of file to delete"""
        async for grid_data in fs.find():
            fid = grid_data._id
            write_log(FILES_LOGGER, 'debug', 'mongo file handler', f'Deleting file with id: {fid}')
            await fs.delete(fid)


class FolderStorage:
    @staticmethod
    async def save_file(upload_file: UploadFile) -> str:
        """
        Save the file to the "storage/private" folder.
        params:
            file: file-like object
        return:
            returns id of the file
        """
        # splits file name and extension for example: myFile.txt => myFile,.txt
        filename, file_extension = os.path.splitext(upload_file.filename)
        file_id = unique_string_gen() + file_extension
        async with aiofiles.open(os.path.join('storage', 'private', file_id), 'wb') as out_file:
            content = await upload_file.read()
            await out_file.write(content)
            write_log(FILES_LOGGER, 'debug', 'folder file handler',
                      f'saving file with id: {file_id} and name: {upload_file.filename}')
            return str(file_id)

    @staticmethod
    async def delete_file(file_id) -> None:
        """Get _id of file to delete from "storage/private" folder"""
        write_log(FILES_LOGGER, 'debug', 'folder file handler', f'Deleting file with id: {file_id}')
        await aiofileos.remove(os.path.join('storage', 'private', file_id))
