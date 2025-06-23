import importlib
import pkgutil
import inspect
import traceback
from typing import AsyncGenerator, Any, Dict, List, Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import create_engine, and_, or_, not_, text

from app.core.database import Base

class DBClient:
    def __init__(self, session: AsyncSession):
        self.session = session

    """
    @classmethod
    async def get_db(cls) -> AsyncGenerator["DBClient", None]:
        async for session in get_async_db():
            yield cls(session)
    """

    @staticmethod
    def row_to_dict(row: Any) -> Dict[str, Any]:
        """
        Convert a SQLAlchemy row to a dictionary.
        """
        return {column.name: getattr(row, column.name) for column in row.__table__.columns}
    
    @staticmethod
    def db_model_to_dict(model_instance, columns = None):
        """
        Convert a SQLAlchemy model instance to a dictionary.
        If columns are specified, only those columns will be included.
        """
        if model_instance is None:
            return None
        
        if columns:
            return {column: getattr(model_instance, column) for column in columns}
        
        return {column: getattr(model_instance, column) for column in model_instance.__table__.columns.keys()}
    
    def get_model_class(self, table_name: str) -> Optional[Type]:
        """
        Get the SQLAlchemy model class by table name.
        """
        try:
            models_pkg = importlib.import_module("app.models")
            for finder, name, ispkg in pkgutil.iter_modules(models_pkg.__path__):
                module = importlib.import_module(f"app.models.{name}")
                for attr in dir(module):
                    cls = getattr(module, attr)
                    if (
                        inspect.isclass(cls)
                        and hasattr(cls, "__tablename__")
                        and cls.__tablename__ == table_name
                    ):
                        return cls
        except Exception:
            traceback.print_exc()
        return None
    
    async def query_table_data(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
        single_row: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ):
        """
        Retrieve data from a specified table with optional filters.
        """
        model_class = self.get_model_class(table_name)
        if not model_class:
            return None

        stmt = select(model_class)
        if filters:
            for key, value in filters.items():
                if hasattr(model_class, key):
                    stmt = stmt.where(getattr(model_class, key) == value)

        # apply pagination if specified
        if limit is not None:
            stmt = stmt.limit(limit)

        if offset is not None:
            stmt = stmt.offset(offset)

        # execute the query
        result = await self.session.execute(stmt)
        rows = result.scalars()

        if single_row:
            row = rows.first()
            return self.row_to_dict(row) if row else None

        return [self.row_to_dict(r) for r in rows.all()]
    
    async def create_table_entry(
        self,
        table_name: str,
        data: Dict[str, Any]
    ):
        """
        Create a new entry in the specified table.
        """
        model_class = self.get_model_class(table_name)

        if not model_class:
            return None

        new_entry = model_class(**data)
        self.session.add(new_entry)
        try:
            await self.session.flush()
            await self.session.refresh(new_entry)
            return self.row_to_dict(new_entry)
        except Exception as e:
            traceback.print_exc()
            raise e
        
    async def update_table_entry(
        self,
        table_name: str,
        identifier: Dict[str, Any],
        update_data: Dict[str, Any]
    ):
        """
        Update an existing entry in the specified table.
        """
        model_class = self.get_model_class(table_name)
        if not model_class:
            return None
        
        q = select(model_class)
        for key, value in identifier.items():
            q = q.where(getattr(model_class, key) == value)
        
        result = await self.session.execute(q)
        row = result.scalars().first()

        if not row:
            return None
        for key, value in update_data.items():
            setattr(row, key, value)
        try:
            await self.session.flush()
            await self.session.refresh(row)
            return self.row_to_dict(row)
        except Exception as e:
            traceback.print_exc()
            raise e
