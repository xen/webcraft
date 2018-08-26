import datetime
import decimal
from json import dumps

from aiohttp import web
from sqlalchemy import select, delete, update, insert
from sqlalchemy import desc


def alchemyencoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


class BaseView(web.View):
    model = None
    limit: int = 10
    table_id: str = 'id'

    @property
    def id_field(self):
        return getattr(self.model.c, self.table_id)

    @property
    def item_id(self):
        return self.match_type(self.request.match_info[self.match_name])


class ListView(BaseView):
    async def get(self, query=None):
        async with self.request.app['db'].acquire() as conn:
            if query is None:
                query = select([self.model, ]).order_by(
                    desc(self.id_field)).limit(self.limit + 1)
            records = await conn.fetch(query)
            data = [dict(q) for q in records]

        return web.Response(
            body=dumps(data, default=alchemyencoder),
            content_type='application/json'
        )

    async def post(self, query=None):
        async with self.request.app['db'].acquire() as conn:
            if query is None:
                data = self.request['data']
                query = insert(self.model).values(
                    **data).returning(self.id_field)
            item = await conn.fetchrow(query)

        return web.json_response(
            {'msg': 'Done',
             'data': {'id': item[self.table_id]}}
        )


class ItemView(BaseView):
    model = None
    match_name: str
    match_type: type = int
    table_id = 'id'

    async def get(self, query=None):
        async with self.request.app['db'].acquire() as conn:
            if query is None:
                query = select([self.model, ]).where(
                    self.id_field == self.item_id)
            item = await conn.fetchrow(query)
            if item is None:
                return web.json_response(
                    {'error': 'Not found', 'data': {
                        'id': self.item_id}},
                    status=404
                )

        return web.Response(
            body=dumps(dict(**item), default=alchemyencoder),
            content_type='application/json'
        )

    async def post(self, query):
        data = self.request['data']
        data.pop(self.match_name)
        async with self.request.app['db'].acquire() as conn:
            if query is None:
                query = update(self.model).returning(self.id_field).where(
                    self.id_field == self.item_id).values(**data)
            item = await conn.fetchrow(query)
            if item is None:
                return web.json_response(
                    {'error': 'Not found', 'data': {
                        'id': self.item_id}},
                    status=404
                )

        return web.json_response(
            {'msg': 'Updated',
             'data': {'id': item[self.table_id]}}
        )

    async def delete(self, query):
        # TODO: thid method doesn't check existence of the item in database
        async with self.request.app['db'].acquire() as conn:
            if query is None:
                query = delete(self.model).where(
                    self.id_field == self.item_id)
            await conn.fetchrow(query)
        return web.json_response(
            {'msg': 'Done',
             'data': {'id': self.item_id}}
        )
