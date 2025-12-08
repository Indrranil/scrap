import textwrap

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.utils import gen_util
from app.utils.sql_factory import SQLFactory, SQLQuery

router = APIRouter(prefix="/v1/analytics", tags=["Analytics"])


@router.get("/cumulative-count")
def get_cumulative_count(start_time: int, end_time: int, db: Session = Depends(get_db)):
    query = SQLFactory.get_query(SQLQuery.CUMULATIVE_COUNT, start_time=start_time, end_time=end_time)
    result = db.execute(text(textwrap.shorten(query, 1e8)))
    decoded = [gen_util.format_nested_dict(dict(r)) for r in result.mappings().all()]
    return gen_util.form_generic_response(decoded)
