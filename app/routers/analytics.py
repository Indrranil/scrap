import textwrap

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.utils import gen_util
from app.utils.sql_factory import SQLFactory, SQLQuery

router = APIRouter(prefix="/v1/analytics", tags=["Analytics"])


@router.get("/cumulative-count")
def get_cumulative_count(start_time: int, end_time: int, output_key: str, pipeline_id: str, db: Session = Depends(get_db)):
    query = SQLFactory.get_query(SQLQuery.CUMULATIVE_COUNT, start_time=start_time, end_time=end_time, output_key=output_key, pipeline_id=pipeline_id)
    result = db.execute(text(textwrap.shorten(query, 1e8)))
    decoded = [gen_util.format_nested_dict(dict(r)) for r in result.mappings().all()]
    return gen_util.form_generic_response(decoded)


@router.get("/raw-output")
def get_raw_output_by_pipeline(start_time: int, end_time: int, pipeline_id: int, db: Session = Depends(get_db)):
    query = SQLFactory.get_query(SQLQuery.RAW_OUTPUT, start_time=start_time, end_time=end_time, pipeline_id=pipeline_id)
    result = db.execute(text(textwrap.shorten(query, 1e8)))
    decoded = [gen_util.format_nested_dict(dict(r)) for r in result.mappings().all()]
    return gen_util.form_generic_response(decoded)


@router.get("/output-by-value")
def get_output_by_value(output_key: str, output_value: str, page_no: int = 1, db: Session = Depends(get_db)):
    limit = 50
    offset = (page_no - 1) * limit
    query = SQLFactory.get_query(SQLQuery.OUTPUT_BY_VALUE, output_key=output_key, output_value=output_value, limit=limit, offset=offset)
    result = db.execute(text(textwrap.shorten(query, 1e8)))
    decoded = [gen_util.format_nested_dict(dict(r)) for r in result.mappings().all()]
    return gen_util.form_generic_response(decoded)


@router.get("/cumulative-value")
def get_output_by_value(output_key: str, suffix: str, start_time: int, end_time: int, pipeline_id: int, db: Session = Depends(get_db)):
    query = SQLFactory.get_query(SQLQuery.CUMULATIVE_VALUE, output_key=output_key, suffix=suffix, start_time=start_time, end_time=end_time, pipeline_id=pipeline_id)
    result = db.execute(text(textwrap.shorten(query, 1e8)))
    decoded = [gen_util.format_nested_dict(dict(r)) for r in result.mappings().all()]
    return gen_util.form_generic_response(decoded)
