"""Download a quarter as XLSX (three sheets) or CSV (one sheet)."""

from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.deps import Db
from app.api.errors import error_responses, not_found
from app.api.schemas import ExportFormat, ExportSheet, PlanLanguage
from app.exporters import CsvExporter, Exporter, XlsxExporter
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
