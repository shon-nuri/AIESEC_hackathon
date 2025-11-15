from sqlalchemy import insert
from backend.app.db.database import async_session_maker
from backend.app.models.document import Document


class DocumentsDAO():
    

    @classmethod
    async def add(**data):
        async with async_session_maker() as session:
            query = insert(Document).values(**data)
            await session.execute(query)
            await session.commit()
