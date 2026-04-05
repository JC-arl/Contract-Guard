from pydantic import BaseModel


class Clause(BaseModel):
    index: int
    title: str
    content: str
