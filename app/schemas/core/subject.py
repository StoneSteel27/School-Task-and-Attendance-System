from pydantic import BaseModel


class Subject(BaseModel):
    name: str
    teacher_name: str

    class Config:
        from_attributes = True
