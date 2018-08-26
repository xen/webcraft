from aiohttp import web
# aio-libs
import asyncpgsa
import aiosmtplib
from email.mime.text import MIMEText

# SQLAlchemy core imports
from sqlalchemy import (
    Table, Text, MetaData, String, Integer, Column, Boolean,
    DateTime, insert
)
# Marshmallow to define and validate schema
from marshmallow import Schema, fields

# To get nice working OpenAPI (Swagger) UI
from aiohttp_apispec import AiohttpApiSpec, aiohttp_apispec_middleware
from aiohttp_swagger import setup_swagger

# this part needed to define specs
from aiohttp_apispec import docs, use_kwargs, marshal_with

from webcraft import ItemView, ListView


# Now lets define database
meta = MetaData()
message = Table(
    'message', meta,
    Column('id', Integer(), primary_key=True),
    Column('created_at', DateTime(), nullable=True),
    Column('to_user', String(), index=True, nullable=False),
    Column('from_user', String(), index=True, nullable=False),
    Column('text', Text(), nullable=True),
    Column('is_sent', Boolean(), nullable=True),
)

# Then define Schema


class ErrorSchema(Schema):
    error = fields.Str()
    data = fields.Dict()


class MessageSchema(Schema):
    from_user = fields.Str()
    to_user = fields.Str()
    text = fields.Raw()
    is_sent = fields.Bool()


class MessageItemSchema(MessageSchema):
    id = fields.Int()
    created_at = fields.DateTime()

# index page redirect to the /api-doc/ page

async def index(request):
    return web.HTTPFound('/api-doc/')

# And class based views

class MessageListView(ListView):
    # here
    model = message

    @docs(
        tags=['Messages'],
        summary='List messages',
        description='List all messages',
    )
    @marshal_with(MessageItemSchema(many=True), 200)
    async def get(self):
        return await super().get()


class MessageItemView(ItemView):
    model = message
    match_name = 'message_id'

    @docs(
        tags=['Messages'],
        summary='Get one message item',
        description='Get full message information',
    )
    @marshal_with(MessageSchema(), 200)
    @marshal_with(ErrorSchema(), 404)
    async def get(self):
        return await super().get()


class SendView(web.View):
    @docs(
        tags=['Messenger'],
        summary='Process messenger actions ',
        description='Send message to user',
    )
    @marshal_with(MessageSchema(many=True), 200)
    async def post(self):
        data = self.request['data']
        msg = MIMEText(data['text'])
        msg['From'] = data['from_user']
        msg['To'] = data['to_user']
        msg['Subject'] = data['text'][0:30]

        await request.app['smtp'].send_message(msg)

        async with self.request.app['db'].acquire() as conn:
            query = insert(message).values(
                **data).returning(message.c.id)
            item = await conn.fetchrow(query)

        return web.json_response(
            {'msg': 'Done',
             'data': {'id': item['id']}
             }
        )

# init application extensions


async def on_start_app(app):
    config = app['config']
    app['db'] = await asyncpgsa.create_pool(dsn=config['database_uri'])
    app['smtp'] = aiosmtplib.SMTP(
        hostname=config['smtp']['hostname'],
        port=config['smtp']['port']
    )
    setup_swagger(
        app=app,
        swagger_url='/api-doc',
        swagger_info=app['swagger_dict'],
        api_base_url='/api/',
    )
    # for resource in app.router.resources():
    #     print(resource)


async def on_cleanup_app(app):
    await app['db'].close()

# define app object
app = web.Application()

config = {
    'database_uri': 'postgresql://localhost:5432/notify',
    'smtp': {
        'hostname': 'localhost',
        'port': 1025
    }
}
app['config'] = config

# routes
app.add_routes([web.get('/', index)])

# messages API
app.router.add_view('/api/messages', MessageListView)
app.router.add_view(
    '/api/messages/{message_id:\d+}', MessageItemView)

# process API
app.router.add_view('/api/send', SendView)
AiohttpApiSpec(
    app=app,
    title='Notify API Documentation',
    description="Notification service API specification",
    version='v1',
    url='/api-doc/swagger.json',
)

app.middlewares.append(aiohttp_apispec_middleware)

app.on_startup.append(on_start_app)
app.on_cleanup.append(on_cleanup_app)

web.run_app(app)
