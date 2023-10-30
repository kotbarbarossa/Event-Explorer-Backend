import logging
from typing import Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, join
from database import get_db
from get_osm_response import (get_sustenance_by_position,
                              get_places_by_id, get_search_by_name,
                              get_place_by_id)

from models import Command, Message, User, Event, Place, place_user_association

app = FastAPI(
    title='Event-Explorer-Backend',
    debug=True
)

tm = datetime.now().strftime("%H:%M")


@app.get('/', tags=[
    f'Привет покоритель космических пространств! Время на борту: {tm}'])
def read_root():
    return {'Hello': 'World'}


@app.get('/commands/', tags=['Commands'])
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
    except SQLAlchemyError as e:
        logger.error(f'Ошибка при получении списка пользователей: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


@app.get('/commands/{command}/', tags=['Commands'])
async def get_command(
        command: str,
        telegram_id: str = Query(...),
        db=Depends(get_db)):
    """Функция получения ответа на command."""
    try:
        db_command = db.query(Command).filter_by(command=command).one_or_none()

        if db_command is None:
            try:
                db_command = db.query(Command).filter_by(
                    command='instruction_command_1').one_or_none()
                if db_command is None:
                    error = 'Ошибка при запросе instruction_command_1'
                    logger.error(error)
                    raise HTTPException(status_code=404, detail=error)
            except SQLAlchemyError as e:
                logger.error(f'{error}: {str(e)}')
                raise HTTPException(status_code=500, detail='Database error')

        return {'telegram_id': telegram_id, 'response': db_command.response}

    except SQLAlchemyError as e:
        logger.error(f'Ошибка при получении команды: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


class CommandRequest(BaseModel):
    """Влидация для commands."""
    telegram_id: str
    command: str = Field(max_length=50)
    response: str = Field(max_length=250)


@app.post('/commands/', tags=['Commands'])
async def create_command(request: CommandRequest, db=Depends(get_db)):
    """Функция создания command."""
    telegram_id = request.telegram_id
    command = request.command
    response = request.response

    try:
        new_command = Command(command=command, response=response)
        db.add(new_command)
        db.commit()
        logger.info(f'Команда "{command}" успешно сохранена')
        return {'telegram_id': telegram_id,
                'response': 'Команда успешно создана'}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f'Ошибка при создании команды: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


@app.put('/commands/{command}/', tags=['Commands'])
async def update_command(
        command: str, request: CommandRequest, db=Depends(get_db)):
    """Функция обновления command по id."""
    telegram_id = request.telegram_id
    new_command = request.command
    new_response = request.response

    try:
        db_command = db.query(Command).filter_by(command=command).one_or_none()

        if db_command:
            db_command.command = new_command
            db_command.response = new_response
            db.commit()
            logger.info(f'Команда "{new_command}" успешно изменена')
            return {'telegram_id': telegram_id,
                    'response': 'Команда успешно обновлена'}

        return HTTPException(
            status_code=404, detail='Такой команды не существует')

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f'Ошибка при изменении команды: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


@app.get('/messages/', tags=['Messages'])
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
    except SQLAlchemyError as e:
        logger.error(f'Ошибка при получении списка сообщений: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


@app.get('/messages/{message}/', tags=['Messages'])
async def get_message(
        message: str,
        telegram_id: str = Query(...),
        db=Depends(get_db)):
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
            except SQLAlchemyError as e:
                logger.error(f'Database error: {str(e)}')
                raise HTTPException(status_code=500, detail='Database error')

        return {'telegram_id': telegram_id, 'response': db_message.response}

    except SQLAlchemyError as e:
        logger.error(f'Ошибка при получении сообщения: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


class MessageRequest(BaseModel):
    """Влидация handle_messages."""
    telegram_id: str
    message: str = Field(max_length=250)
    response: str = Field(max_length=1000)


@app.post('/messages/', tags=['Messages'])
async def create_message(request: MessageRequest, db=Depends(get_db)):
    """Функция создания message."""
    telegram_id = request.telegram_id
    message = request.message
    response = request.response

    try:
        new_message = Message(message=message, response=response)
        db.add(new_message)
        db.commit()
        logger.info(f'Сообщение "{message}" успешно создано')
        return {'telegram_id': telegram_id,
                'response': 'Сообщение успешно создано'}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f'Ошибка при создании сообщения: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


@app.put('/messages/{message}/', tags=['Messages'])
async def update_message(
        message: str, request: MessageRequest, db=Depends(get_db)):
    """Функция обновления command по id."""
    telegram_id = request.telegram_id
    new_message = request.message
    new_response = request.response

    try:
        db_message = db.query(Message).filter_by(message=message).one_or_none()

        if db_message:
            db_message.message = new_message
            db_message.response = new_response
            db.commit()
            logger.info(f'Сообщение "{new_message}" успешно изменено')
            return {'telegram_id': telegram_id,
                    'response': 'Сообщение успешно обновлена'}

        return HTTPException(
            status_code=404, detail='Такого сообщения не существует')

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f'Ошибка при изменении сообщения: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


class LocationRequest(BaseModel):
    """Влидация handle_messages."""
    telegram_id: str
    latitude: float
    longitude: float


@app.get('/locations/', tags=['Locations'])
async def get_location(
        telegram_id: str = Query(...),
        latitude: str = Query(...),
        longitude: str = Query(...),
        db=Depends(get_db)):
    """Функция отображения location."""
    around = 200
    current_time = datetime.now()
    locations = await get_sustenance_by_position(latitude, longitude, around)
    if locations.get('error'):
        logger.error('Ошибка при запросе overpass-api.de')
        raise HTTPException(
                status_code=404,
                detail='Ошибка при запросе локаций')
    for location in locations['elements']:
        place_id = str(location['id'])

        events_in_location = (
            db.query(Event, User.telegram_username)
            .join(User, Event.user_id == User.telegram_id)
            .filter(
                Event.place_id == place_id,
                Event.end_datetime > current_time)
            .all()
        )

        if events_in_location:
            events_info = []
            for event, telegram_username in events_in_location:
                event_info = {
                    'name': event.name,
                    'description': event.description,
                    'place_id': event.place_id,
                    'end_datetime': event.end_datetime,
                    'id': event.id,
                    'user_id': event.user_id,
                    'start_datetime': event.start_datetime,
                    'comment': event.comment,
                    'telegram_username': telegram_username,
                    'event_participants': event.participants
                }
                events_info.append(event_info)

            location['events'] = events_info

    return {'telegram_id': telegram_id, 'response': locations}


@app.get('/locations/search/', tags=['Locations'])
async def get_location_search_by_name(
        telegram_id: str = Query(...),
        region_name: str = Query(...),
        place_name: str = Query(...),
        db=Depends(get_db)):
    """Функция отображения поиска location."""
    current_time = datetime.now()
    locations = await get_search_by_name(region_name, place_name)
    if locations.get('error'):
        logger.error('Ошибка при запросе overpass-api.de')
        raise HTTPException(
                status_code=404,
                detail='Ошибка при запросе локаций')
    for location in locations['elements']:
        place_id = str(location['id'])
        events_in_location = (
            db.query(Event, User.telegram_username)
            .join(User, Event.user_id == User.telegram_id)
            .filter(
                Event.place_id == place_id,
                Event.end_datetime > current_time)
            .all()
        )

        if events_in_location:
            events_info = []
            for event, telegram_username in events_in_location:
                event_info = {
                    'name': event.name,
                    'description': event.description,
                    'place_id': event.place_id,
                    'end_datetime': event.end_datetime,
                    'id': event.id,
                    'user_id': event.user_id,
                    'start_datetime': event.start_datetime,
                    'comment': event.comment,
                    'telegram_username': telegram_username,
                    'event_participants': event.participants
                }
                events_info.append(event_info)

            location['events'] = events_info

    return {'telegram_id': telegram_id, 'response': locations}


@app.get('/places/{place_id}/', tags=['Places'])
async def get_place_detail(
        place_id: str,
        telegram_id: str = Query(...),
        db=Depends(get_db)):
    """Функция отображения поиска place detail."""
    current_time = datetime.now()
    locations = await get_place_by_id(place_id=place_id)
    if locations.get('error'):
        logger.error('Ошибка при запросе overpass-api.de')
        raise HTTPException(
                status_code=404,
                detail='Ошибка при запросе локации')
    location = locations['elements'][0]
    place_id = str(location['id'])

    events_in_location = (
        db.query(Event, User.telegram_username)
        .join(User, Event.user_id == User.telegram_id)
        .filter(
            Event.place_id == place_id,
            Event.end_datetime > current_time)
        .all()
    )

    if events_in_location:
        events_info = []
        for event, telegram_username in events_in_location:
            event_info = {
                'name': event.name,
                'description': event.description,
                'place_id': event.place_id,
                'end_datetime': event.end_datetime,
                'id': event.id,
                'user_id': event.user_id,
                'start_datetime': event.start_datetime,
                'comment': event.comment,
                'telegram_username': telegram_username,
                'event_participants': event.participants
            }
            events_info.append(event_info)

        location['events'] = events_info

    return {'telegram_id': telegram_id, 'response': locations}


@app.get('/users/', tags=['Users'])
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
        db.rollback()
        logger.error(f'Ошибка при получении списка пользователей: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


@app.get('/users/{telegram_id}/', tags=['Users'])
async def get_user(
        telegram_id: str,
        db=Depends(get_db)):
    """Функция получения user."""
    try:
        db_user = db.query(User).filter_by(
            telegram_id=telegram_id).one_or_none()

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
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f'Ошибка при получении пользоватея {telegram_id}: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


class UserRequest(BaseModel):
    """Влидация handle_messages."""
    telegram_id: str
    username: Optional[str]
    role: str = 'participant'
    first_name: Optional[str]
    last_name: Optional[str]
    language_code: Optional[str]
    is_bot: bool


@app.post('/users/', tags=['Users'])
async def create_user(request: UserRequest, db=Depends(get_db)):
    """Функция создания user."""
    telegram_id = request.telegram_id
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
        logger.info(
            f'Пользователь "{telegram_id}" - '
            f'"{telegram_username}" успешно создан')
        return {
            'telegram_id': telegram_id,
            'response': 'Пользователь успешно создан'}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f'Ошибка при создании пользователя {telegram_id}: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


@app.put('/users/{telegram_id}/', tags=['Users'])
async def update_user(
        telegram_id: str, request: UserRequest, db=Depends(get_db)):
    """Функция обновления user по telegram_id."""
    new_telegram_username = request.username
    new_first_name = request.first_name
    new_last_name = request.last_name
    new_language_code = request.language_code

    try:
        db_user = db.query(User).filter_by(
            telegram_id=telegram_id).one_or_none()

        if db_user:
            db_user.telegram_username = new_telegram_username
            db_user.first_name = new_first_name
            db_user.last_name = new_last_name
            db_user.language_code = new_language_code
            db.commit()
            logger.info(
                f'Пользователь "{telegram_id}" - '
                f'"{new_telegram_username}" изменен')
            return {'telegram_id': telegram_id,
                    'response': 'Сообщение успешно обновлена'}

        return HTTPException(
            status_code=404, detail='Такого сообщения не существует')

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f'Ошибка при изменении пользователя {telegram_id}: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


@app.get('/users/places/subscription/', tags=['Users places subscription'])
async def get_all_places_subscription(db=Depends(get_db)):
    """Функция получения всех places subscription."""
    try:
        users = db.query(User).all()

        if not users:
            raise HTTPException(
                status_code=404,
                detail='Нет доступных подписок на места')

        events_data = []
        for user in users:
            user_dict = {
                "telegram_id": user.telegram_id,
                "telegram_username": user.telegram_username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "favorite_places": []
            }
            if user.favorite_places:
                for place in user.favorite_places:
                    place_dict = {
                        'place_id': place.place_id,
                        'places_name': place.name
                    }
                    user_dict['favorite_places'].append(place_dict)
            events_data.append(user_dict)

        return events_data
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f'Ошибка при получении списка подписок на места: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


@app.get('/users/{telegram_id}/places/subscription/',
         tags=['Users places subscription'])
async def get_user_places_subscription(
        telegram_id: str,
        db=Depends(get_db)):
    """Функция получения подписок на place."""
    try:
        user_places_subscription = (
            db.query(place_user_association.c.place_id)
            .select_from(
                join(
                    User,
                    place_user_association,
                    User.telegram_id == place_user_association.c.user_id)
            )
            .filter(User.telegram_id == telegram_id)
        )

        place_ids = [result[0] for result in user_places_subscription.all()]

        if not place_ids:
            # try:
            #     db_message = db.query(Message).filter_by(
            #         message='places_sub_instruction_1').one_or_none()
            #     if db_message is None:
            error = 'Ошибка при запросе places_sub_instruction_1'
            logger.error(error)
            raise HTTPException(status_code=404, detail=error)
            #     return {'telegram_id': telegram_id,
            #             'response': db_message.response}
            # except SQLAlchemyError as e:
            #     logger.error(f'error: {str(e)}')
            #     raise HTTPException(status_code=500, detail='Database error')

        current_time = datetime.now()
        locations = await get_places_by_id(place_ids)
        if locations.get('error'):
            logger.error('Ошибка при запросе overpass-api.de')
            raise HTTPException(
                    status_code=404,
                    detail='Ошибка при запросе локаций')
        for location in locations['elements']:
            place_id = str(location['id'])

            events_in_location = (
                db.query(Event, User.telegram_username)
                .join(User, Event.user_id == User.telegram_id)
                .filter(
                    Event.place_id == place_id,
                    Event.end_datetime > current_time)
                .all()
            )

            if events_in_location:
                events_info = []
                for event, telegram_username in events_in_location:
                    event_info = {
                        'name': event.name,
                        'description': event.description,
                        'place_id': event.place_id,
                        'end_datetime': event.end_datetime,
                        'id': event.id,
                        'user_id': event.user_id,
                        'start_datetime': event.start_datetime,
                        'comment': event.comment,
                        'telegram_username': telegram_username,
                        'event_participants': event.participants
                    }
                    events_info.append(event_info)

                location['events'] = events_info

        return {'telegram_id': telegram_id, 'response': locations}

    except SQLAlchemyError as e:
        logger.error(f'Ошибка при получении команды: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


class PlaceSubscriptionRequest(BaseModel):
    """Влидация create_place_subscription."""
    telegram_id: str
    place_id: str


@app.post('/users/places/subscription/', tags=['Users places subscription'])
async def create_place_subscription(
        request: PlaceSubscriptionRequest,
        db=Depends(get_db)):
    """Функция создания подписки на place."""
    telegram_id = request.telegram_id
    place_id = request.place_id

    try:

        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        place = db.query(Place).filter_by(place_id=place_id).first()
        if not place:
            place = Place(place_id=place_id)
            db.add(place)
            db.commit()

        if user is not None:
            user.favorite_places.append(place)
            db.commit()
            logger.info(
                f'Пользователь:"{telegram_id}" '
                f'Добавил место id:"{place_id}" в избранное')
            return {
                'user_id': telegram_id,
                'place_id': place_id,
                'response': 'Добавлено в избранное'}
        else:
            error = 'Пользователь не найден'
            logger.error(error)
            raise HTTPException(status_code=404, detail=error)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f'Ошибка при добавление места в избранное: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


@app.delete('/users/{telegram_id}/places/subscription/',
            tags=['Users places subscription'])
async def delete_user_place_subscription(
        telegram_id: str,
        place_id: str = Query(...),
        db=Depends(get_db)):
    """Функция удаления подписки на place."""

    try:
        user = db.query(User).filter(
            User.telegram_id == telegram_id,
            User.favorite_places.any(Place.place_id == place_id)
        ).one_or_none()

        if user:
            place = db.query(Place).filter(Place.place_id == place_id).first()
            if place:
                user.favorite_places.remove(place)
                db.commit()
                logger.info(
                    f'Пользователь:"{telegram_id}" '
                    f'Удалил место id:"{place_id}" из избранного')
                return {
                    'user_id': telegram_id,
                    'place_id': place_id,
                    'response': 'Удалено избранное'}
        else:
            error = 'Подписка не найдена'
            logger.error(error)
            raise HTTPException(status_code=404, detail=error)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f'Ошибка при удалении места из избранного: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


@app.get('/users/{telegram_id}/subscription/', tags=['Users subscription'])
async def get_user_subscription(
        telegram_id: str,
        db=Depends(get_db)):
    """Функция получения подписок пользователей."""
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).one_or_none()
        subscriptions = [{
            'telegram_id': user.telegram_id,
            'telegram_username': user.telegram_username
            } for user in user.subscriptions]
        return {'telegram_id': telegram_id, 'response': subscriptions}

    except SQLAlchemyError as e:
        logger.error(
            f'Ошибка при получении списка подписок пользователя: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


class UserSubscriptionRequest(BaseModel):
    """Влидация create_user_subscription."""
    telegram_id: str
    subscription_id: str


@app.post('/users/subscription/', tags=['Users subscription'])
async def create_user_subscription(
        request: UserSubscriptionRequest,
        db=Depends(get_db)):
    """Функция создания подписки на User."""
    telegram_id = request.telegram_id
    subscription_id = request.subscription_id

    try:

        telegram_user = db.query(User).filter_by(
            telegram_id=telegram_id).one_or_none()
        subscription_user = db.query(User).filter_by(
            telegram_id=subscription_id).one_or_none()

        if telegram_user and subscription_user:
            if telegram_user == subscription_user:
                return {'error': 'Нельзя подписываться на самого себя!'}
            telegram_user.subscriptions.append(subscription_user)
            db.commit()
            logger.info(
                f'Пользователь:"{telegram_id}" '
                f'Подписался на:"{subscription_id}"')
            return {
                'telegram_id': telegram_id,
                'subscription_id': subscription_id,
                'response': 'Подписка прошла удачно'}
        else:
            error = 'Пользователь не найден'
            logger.error(error)
            raise HTTPException(status_code=404, detail=error)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f'Ошибка при добавление пользователя в избранное: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


@app.delete('/users/{telegram_id}/subscription/', tags=['Users subscription'])
async def delete_user_subscription(
        telegram_id: str,
        subscription_id: str = Query(...),
        db=Depends(get_db)):
    """Функция удаления подписок пользователей."""
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).one_or_none()
        subscription = db.query(User).filter_by(
            telegram_id=subscription_id).one_or_none()
        if user and subscription:
            if subscription in user.subscriptions:
                user.subscriptions.remove(subscription)
                db.commit()
                return {'telegram_id': telegram_id,
                        'response': f'Подписка на {subscription_id} удалена'}
            else:
                error = 'Подписка не найдена'
                logger.error(error)
                raise HTTPException(status_code=404, detail=error)
        else:
            error = 'Пользователь не найден'
            logger.error(error)
            raise HTTPException(status_code=404, detail=error)

    except SQLAlchemyError as e:
        logger.error(
            f'Ошибка при получении списка подписок пользователя: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


class EventSubscriptionRequest(BaseModel):
    """Влидация create_event_subscription."""
    telegram_id: str
    event_id: int


@app.post('/users/events/subscription/', tags=['Users events subscription'])
async def create_event_subscription(
        request: EventSubscriptionRequest,
        db=Depends(get_db)):
    """Функция создания подписки на event."""
    telegram_id = request.telegram_id
    event_id = request.event_id

    try:

        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        event = db.query(Event).filter_by(id=event_id).first()

        if user is not None and event is not None:
            user.events_participated.append(event)
            db.commit()
            logger.info(
                f'Участие пользователя:"{telegram_id}" '
                f'в событии id:"{event_id}" успешно создано')
            return {
                'user_id': telegram_id,
                'event_id': event_id,
                'response': 'Участие подтверждено'}
        else:
            error = 'Пользователь или событие не найдены'
            logger.error(error)
            raise HTTPException(status_code=404, detail=error)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f'Ошибка при создании подписки на событие: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


async def is_event_finished(event):
    current_time = datetime.now()
    return event < current_time


@app.get('/events/', tags=['Events'])
async def get_all_events(db=Depends(get_db)):
    """Функция получения всех Events."""
    try:
        events = db.query(Event).order_by(desc(Event.start_datetime)).all()

        if not events:
            raise HTTPException(
                status_code=404,
                detail='Нет доступных событий')

        events_data = [{
            'id': event.id,
            'name': event.name,
            'description': event.description,
            'user_id': event.user_id,
            'place_id': event.place_id,
            'start_datetime': event.start_datetime,
            'end_datetime': event.end_datetime,
            'comment': event.comment,
            'is_finished': await is_event_finished(event.end_datetime),
            } for event in events]

        return events_data
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f'Ошибка при получении списка событий: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


class EventRequest(BaseModel):
    """Влидация create_event."""
    name: str = Field(max_length=50)
    description: str
    telegram_id: str
    place_id: str = Field(max_length=250)
    start_datetime: str
    end_datetime: str


@app.post('/events/', tags=['Events'])
async def create_event(request: EventRequest, db=Depends(get_db)):
    """Функция создания event."""
    name = request.name
    description = request.description
    telegram_id = request.telegram_id
    place_id = request.place_id
    start_datetime = request.start_datetime
    end_datetime = request.end_datetime
    date_format = "%Y-%m-%dT%H:%M:%S.%f"

    try:
        existing_place = db.query(Place).filter(
            Place.place_id == place_id).one_or_none()

        if existing_place:
            place = existing_place
        else:
            place = Place(place_id=place_id)

        new_event = Event(
            name=name,
            description=description,
            user_id=telegram_id,
            place=place,
            start_datetime=datetime.strptime(start_datetime, date_format),
            end_datetime=datetime.strptime(end_datetime, date_format)
        )

        db.add(new_event)
        db.commit()

        logger.info(f'Событие "{name}" в "{place_id}" успешно создано')

        return {'telegram_id': telegram_id,
                'response': 'Событие успешно создано'}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f'Ошибка при создании события: {str(e)}')
        raise HTTPException(status_code=500, detail='Database error')


if __name__ == '__main__':

    logger = logging.getLogger('backend_main_logger')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler('backend_main.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # handler = logging.StreamHandler()
    # handler.setFormatter(formatter)
    # logger.addHandler(handler)

    # async def log_request(request: Request, call_next):
    #     body = await request.body()
    #     logger.info(
    #         f"Request: {request.method} {request.url} - '
    #         f'Body: {body.decode()}")
    #     response = await call_next(request)
    #     return response

    # app.middleware("http")(log_request)

    uvicorn.run(app, host="0.0.0.0", port=8000)
