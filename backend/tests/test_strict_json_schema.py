from pydantic import BaseModel

from app.planner_llm.providers.base import strict_json_schema


class _Task(BaseModel):
    local_id: str
    title: str
    estimate_hours: float
    depends_on: list[str] = []


class _Plan(BaseModel):
    kr_id: str
    tasks: list[_Task]


def test_every_object_is_strict() -> None:
    schema = strict_json_schema(_Plan)
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"kr_id", "tasks"}
    task_schema = schema["$defs"]["_Task"]
    assert task_schema["additionalProperties"] is False
    assert set(task_schema["required"]) == {"local_id", "title", "estimate_hours", "depends_on"}
