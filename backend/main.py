import uvicorn
from fastapi import FastAPI, HTTPException, Depends  # , Request
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from database import get_db

from models import Command, Message

app = FastAPI(
    title='Event-Explorer-Backend'
)


def get_db_session(db=Depends(get_db)):
    """Функция зависимости для получения сессии базы данных."""
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/commands/{command}")
async def get_command(chat_id: int, command: str, db=Depends(get_db_session)):
    """Функция получения ответа на command."""
    try:
        db_command = db.query(Command).filter_by(command=command).one_or_none()

        if db_command is None:
            raise HTTPException(
                status_code=404, detail="Такой команды не существует")

        return {"chat_id": chat_id, "response": db_command.response}

    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/admin/commands_list/")
async def get_all_commands(db=Depends(get_db_session)):
    """Функция получения всех command."""
    try:
        commands = db.query(Command).all()

        if not commands:
            raise HTTPException(status_code=404, detail="Нет доступных команд")

        commands_data = [{
            "id": command.id,
            "command": command.command,
            "response": command.response
            } for command in commands]

        return commands_data
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")


class CommandRequest(BaseModel):
    """Влидация для commands."""
    chat_id: int
    command: str = Field(max_length=50)
    response: str = Field(max_length=250)


@app.post("/admin/commands/")
async def create_command(request: CommandRequest, db=Depends(get_db_session)):
    """Функция создания command."""
    chat_id = request.chat_id
    command = request.command
    response = request.response

    try:
        new_command = Command(command=command, response=response)
        db.add(new_command)
        db.commit()

        return {"chat_id": chat_id, "response": "Команда успешно создана"}

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")


@app.put("/admin/commands/{command_id}")
async def update_command(
        command_id: int, request: CommandRequest, db=Depends(get_db_session)):
    """Функция обновления command по id."""
    chat_id = request.chat_id
    new_command = request.command
    new_response = request.response

    try:
        db_command = db.query(Command).filter_by(id=command_id).first()

        if db_command:
            db_command.command = new_command
            db_command.response = new_response
            db.commit()
            return {"chat_id": chat_id,
                    "response": "Команда успешно обновлена"}

        return HTTPException(
            status_code=404, detail="Такой команды не существует")

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")


class MessageRequest(BaseModel):
    """Влидация handle_messages."""
    chat_id: int
    message: str = Field(max_length=250)


@app.post("/messages/")
async def handle_messages(request: MessageRequest, db=Depends(get_db_session)):
    """Представление для messages."""
    chat_id = request.chat_id
    message = request.message

    try:
        db_message = db.query(Message).filter_by(message=message).one_or_none()

        if db_message is None:
            return {"chat_id": chat_id, "response": "Такие дела"}
        else:
            return {"chat_id": chat_id, "response": db_message.response}

    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
