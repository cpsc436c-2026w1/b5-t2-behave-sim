"""Generative AI shape: questions that users send to an assistant about research papers, one event per question."""
from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, field_validator


class QuestionAsked(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_type: Literal["question_asked"]
    event_time: AwareDatetime
    question_id: str                   # the entity key: one eval case
    work_id: str                       # the OpenAlex work the question is about
    question: str

    @field_validator("event_time")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        if value.utcoffset().total_seconds() != 0:
            raise ValueError("must be UTC (end the time with Z)")
        return value


class Answer(BaseModel):
    """One line of _truth/answers.jsonl: the expected answer of a question, known before the system runs."""
    model_config = ConfigDict(extra="forbid")

    event_id: str
    question_id: str
    answer: str | int


EVENTS = {"question_asked": QuestionAsked}
