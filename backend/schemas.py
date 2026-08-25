from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class DealStatusUpdate(BaseModel):
    status: str


class NoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class DealAssignment(BaseModel):
    salesperson: str = Field(min_length=1, max_length=100)