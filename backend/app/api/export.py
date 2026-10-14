"""Download a quarter as XLSX (three sheets) or CSV (one sheet)."""

from datetime import time
from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.deps import Db
from app.api.errors import error_responses, not_found
from app.api.schemas import DondonSqlExportRequest, ExportFormat, ExportSheet, PlanLanguage
from app.exporters import (
    CsvExporter,
    DondonSqlExporter,
    DondonSqlOptions,
    Exporter,
    XlsxExporter,
)
from app.exporters.dondon_sql import SQL_MEDIA_TYPE
from app.exporters.formats import CSV_MEDIA_TYPE, XLSX_MEDIA_TYPE
from app.persistence.models import Quarter
from app.services.export import export_data

router = APIRouter(tags=["export"])
_BINARY = {"schema": {"type": "string", "format": "binary"}}


@router.get(
    "/quarters/{quarter_id}/export",
    response_class=Response,
    responses={
        200: {
            "description": "The file, sent as an attachment",
            "content": {XLSX_MEDIA_TYPE: _BINARY, CSV_MEDIA_TYPE: _BINARY},
        },
        **error_responses(404, 422),
    },
)
def export_quarter(
    quarter_id: int,
    session: Db,
    file_format: Annotated[ExportFormat, Query(alias="format")] = ExportFormat.xlsx,
    sheet: Annotated[
        ExportSheet, Query(description="CSV only: which table to write")
    ] = ExportSheet.tasks,
    lang: Annotated[PlanLanguage, Query(description="Language of headers and values")] = (
        PlanLanguage.vi
    ),
    details: Annotated[bool, Query(description="Add done criteria and dependencies")] = False,
) -> Response:
    """XLSX has three sheets: tasks, daily schedule and weekly workload. Hours come from the
    latest stored schedule; dates are ISO. Never contains passwords or API keys."""
    quarter = session.get(Quarter, quarter_id)
    if quarter is None:
        raise not_found("quarter", quarter_id)
    data = export_data(session, quarter, lang.value, details=details)
    exporter: Exporter
    name = f"okr-q{quarter.number}-{quarter.year}"
    if file_format == ExportFormat.xlsx:
        exporter = XlsxExporter()
    else:
        exporter = CsvExporter(sheet.value)
        name = f"{name}-{sheet.value}"
    return Response(
        content=exporter.render(data),
        media_type=exporter.media_type,
        headers={"Content-Disposition": f'attachment; filename="{name}.{exporter.extension}"'},
    )


@router.post(
    "/quarters/{quarter_id}/export/dondon-sql",
    response_class=Response,
    responses={
        200: {
            "description": "MySQL script, sent as an attachment",
            "content": {SQL_MEDIA_TYPE: _BINARY},
        },
        **error_responses(404, 422),
    },
)
def export_dondon_sql(quarter_id: int, body: DondonSqlExportRequest, session: Db) -> Response:
    """A script that adds the quarter's tasks to the Inbox of one dondon account, tagged.

    POST so the email stays out of URLs and logs. Nothing is sent to dondon: the file is meant
    to be run by hand in its database.
    """
    quarter = session.get(Quarter, quarter_id)
    if quarter is None:
        raise not_found("quarter", quarter_id)
    hour, minute = (int(part) for part in body.work_start.split(":"))
    exporter = DondonSqlExporter(
        DondonSqlOptions(
            email=body.email,
            tag_name=body.tag_name,
            work_start=time(hour, minute),
            utc_offset_minutes=body.utc_offset_minutes,
            map_priority=body.map_priority,
            keep_status=body.keep_status,
        )
    )
    data = export_data(session, quarter, "vi")
    name = f"okr-q{quarter.number}-{quarter.year}-dondon"
    return Response(
        content=exporter.render(data),
        media_type=exporter.media_type,
        headers={"Content-Disposition": f'attachment; filename="{name}.{exporter.extension}"'},
    )
