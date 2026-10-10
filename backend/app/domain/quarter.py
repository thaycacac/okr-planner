from datetime import date

from pydantic import BaseModel, Field


class Quarter(BaseModel):
    year: int = Field(ge=2000, le=2100)
    number: int = Field(ge=1, le=4)

    @property
    def start(self) -> date:
        return date(self.year, 3 * (self.number - 1) + 1, 1)

    @property
    def end(self) -> date:
        if self.number == 4:
            return date(self.year, 12, 31)
        next_start = date(self.year, 3 * self.number + 1, 1)
        return date.fromordinal(next_start.toordinal() - 1)
