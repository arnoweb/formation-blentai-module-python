from apiflask import Schema
from apiflask.fields import String


class HealthOut(Schema):
    status = String()
    database = String()