import logging
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from database import get_db
from get_osm_response import get_sustenance_by_position

from models import Command, Message, User

app = FastAPI(
    title='Event-Explorer-Backend',
    debug=True
)


@app.get('/')
def read_root():
    return {'Hello': 'World'}


@app.get('/admin/commands_list/')
async def get_all_commands(db=Depends(get_db)):
    """Функция получения всех command."""
    try:
        commands = db.query(Command).all()

        if not commands:
            raise HTTPException(status_code=404, detail='Нет доступных команд')

        commands_data = [{
            'id': command.id,
            'command': command.command,
            'response': command.response
            } for command in commands]

        return commands_data
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail='Database error')


@app.get('/commands/{command}')
async def get_command(chat_id: str, command: str, db=Depends(get_db)):
    """Функция получения ответа на command."""
    try:
        db_command = db.query(Command).filter_by(command=command).one_or_none()

        if db_command is None:
            try:
                db_command = db.query(Command).filter_by(
                    command='instruction_command_1').one_or_none()
                if db_command is None:
                    raise HTTPException(
                        status_code=404,
                        detail='Ошибка при запросе instruction_command_1')
            except SQLAlchemyError:
                raise HTTPException(status_code=500, detail='Database error')

        return {'chat_id': chat_id, 'response': db_command.response}

    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail='Database error')


class CommandRequest(BaseModel):
    """Влидация для commands."""
    chat_id: str
    command: str = Field(max_length=50)
    response: str = Field(max_length=250)


@app.post('/admin/commands/')
async def create_command(request: CommandRequest, db=Depends(get_db)):
    """Функция создания command."""
    chat_id = request.chat_id
    command = request.command
    response = request.response

    try:
        new_command = Command(command=command, response=response)
        db.add(new_command)
        db.commit()

        return {'chat_id': chat_id, 'response': 'Команда успешно создана'}

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail='Database error')


@app.put('/admin/commands/{command_id}')
async def update_command(
        command_id: int, request: CommandRequest, db=Depends(get_db)):
    """Функция обновления command по id."""
    chat_id = request.chat_id
    new_command = request.command
    new_response = request.response

    try:
        db_command = db.query(Command).filter_by(id=command_id).one_or_none()

        if db_command:
            db_command.command = new_command
            db_command.response = new_response
            db.commit()
            return {'chat_id': chat_id,
                    'response': 'Команда успешно обновлена'}

        return HTTPException(
            status_code=404, detail='Такой команды не существует')

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail='Database error')


@app.get('/admin/messages_list/')
async def get_all_messages(db=Depends(get_db)):
    """Функция получения всех message."""
    try:
        messages = db.query(Message).all()

        if not messages:
            raise HTTPException(
                status_code=404,
                detail='Нет доступных сообщений')

        messages_data = [{
            'id': message.id,
            'message': message.message,
            'response': message.response
            } for message in messages]

        return messages_data
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail='Database error')


@app.get('/messages/{message}')
async def get_message(chat_id: str, message: str, db=Depends(get_db)):
    """Функция получения ответа на message."""
    try:
        db_message = db.query(Message).filter_by(message=message).one_or_none()

        if db_message is None:
            try:
                db_message = db.query(Message).filter_by(
                    message='instruction_2').one_or_none()
                if db_message is None:
                    raise HTTPException(
                        status_code=404,
                        detail='Ошибка при запросе instruction_2')
            except SQLAlchemyError:
                raise HTTPException(status_code=500, detail='Database error')

        return {'chat_id': chat_id, 'response': db_message.response}

    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail='Database error')


class MessageRequest(BaseModel):
    """Влидация handle_messages."""
    chat_id: str
    message: str = Field(max_length=250)
    response: str = Field(max_length=1000)


@app.post('/admin/messages/')
async def create_message(request: MessageRequest, db=Depends(get_db)):
    """Функция создания message."""
    chat_id = request.chat_id
    message = request.message
    response = request.response

    try:
        new_message = Message(message=message, response=response)
        db.add(new_message)
        db.commit()

        return {'chat_id': chat_id, 'response': 'Сообщение успешно создано'}

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail='Database error')


@app.put('/admin/messages/{message_id}')
async def update_message(
        message_id: int, request: MessageRequest, db=Depends(get_db)):
    """Функция обновления command по id."""
    chat_id = request.chat_id
    new_message = request.message
    new_response = request.response

    try:
        db_message = db.query(Message).filter_by(id=message_id).one_or_none()

        if db_message:
            db_message.message = new_message
            db_message.response = new_response
            db.commit()
            return {'chat_id': chat_id,
                    'response': 'Сообщение успешно обновлена'}

        return HTTPException(
            status_code=404, detail='Такого сообщения не существует')

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail='Database error')


class LocationRequest(BaseModel):
    """Влидация handle_messages."""
    chat_id: str
    latitude: float
    longitude: float


@app.get('/location/')
async def get_location(chat_id, latitude, longitude):
    """Функция отображения location."""
    # chat_id = request.chat_id
    # latitude = request.latitude
    # longitude = request.longitude
    around = 200
    locations = await get_sustenance_by_position(latitude, longitude, around)
    return {'chat_id': chat_id, 'response': locations}


@app.get('/users/{chat_id}')
async def get_user(chat_id: str, db=Depends(get_db)):
    """Функция получения user."""
    try:
        db_user = db.query(User).filter_by(telegram_id=chat_id).one_or_none()

        if db_user is None:
            raise HTTPException(
                status_code=404,
                detail='Ошибка при запросе user')
        return {
            'id': db_user.id,
            'telegram_id': db_user.telegram_id,
            'telegram_username': db_user.telegram_username,
            'role': db_user.role,
            'first_name': db_user.first_name,
            'last_name': db_user.last_name,
            'language_code': db_user.language_code,
            'is_bot': db_user.is_bot,
            'created_date': db_user.created_date,
            'modified_date': db_user.modified_date,
            }
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail='Database error')


@app.get('/admin/users_list/')
async def get_all_users(db=Depends(get_db)):
    """Функция получения всех user."""
    try:
        users = db.query(User).all()

        if not users:
            raise HTTPException(
                status_code=404,
                detail='Нет доступных пользователей')

        users_data = [{
            'id': user.id,
            'telegram_id': user.telegram_id,
            'telegram_username': user.telegram_username,
            'role': user.role,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'language_code': user.language_code,
            'is_bot': user.is_bot,
            'created_date': user.created_date,
            'modified_date': user.modified_date,
            } for user in users]

        return users_data
    except SQLAlchemyError as e:
        # raise HTTPException(status_code=500, detail='Database error')
        error_message = f'Database error: {str(e)}'
        raise HTTPException(status_code=500, detail=error_message)


class UserRequest(BaseModel):
    """Влидация handle_messages."""
    chat_id: str
    username: Optional[str]
    role: str = 'participant'
    first_name: Optional[str]
    last_name: Optional[str]
    language_code: Optional[str]
    is_bot: bool


@app.post('/users/')
async def create_user(request: UserRequest, db=Depends(get_db)):
    """Функция создания user."""
    telegram_id = request.chat_id
    telegram_username = request.username
    # role = request.role
    first_name = request.first_name
    last_name = request.last_name
    language_code = request.language_code
    is_bot = request.is_bot

    try:
        new_user = User(
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            # role=role,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            is_bot=is_bot,
            )
        db.add(new_user)
        db.commit()

        return {
            'chat_id': telegram_id,
            'response': 'Пользователь успешно создан'}

    except SQLAlchemyError as e:
        db.rollback()
        # raise HTTPException(status_code=500, detail='Database error')
        error_message = f'Database error: {str(e)}'
        raise HTTPException(status_code=500, detail=error_message)


@app.put('/users/{chat_id}')
async def update_user(
        chat_id: str, request: UserRequest, db=Depends(get_db)):
    """Функция обновления user по chat_id."""
    new_telegram_username = request.username
    new_first_name = request.first_name
    new_last_name = request.last_name
    new_language_code = request.language_code

    try:
        db_user = db.query(User).filter_by(telegram_id=chat_id).one_or_none()

        if db_user:
            db_user.telegram_username = new_telegram_username
            db_user.first_name = new_first_name
            db_user.last_name = new_last_name
            db_user.language_code = new_language_code
            db.commit()
            return {'chat_id': chat_id,
                    'response': 'Сообщение успешно обновлена'}

        return HTTPException(
            status_code=404, detail='Такого сообщения не существует')

    except SQLAlchemyError as e:
        db.rollback()
        # raise HTTPException(status_code=500, detail='Database error')
        error_message = f'Database error: {str(e)}'
        raise HTTPException(status_code=500, detail=error_message)


if __name__ == '__main__':
    logging.basicConfig(
        filename='Event_Explorer_back.log',
        format='%(asctime)s - %(name)s - %(levelname)s - LINE: %(lineno)d'
        ' - FUNCTION: %(funcName)s - MESSAGE: %(message)s',
        level=logging.DEBUG,
        filemode='w'
    )

    uvicorn.run(app, host="0.0.0.0", port=8000)
