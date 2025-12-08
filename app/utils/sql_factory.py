import enum


class SQLQuery(enum.Enum):
    CUMULATIVE_COUNT = "cumulative_count"


class SQLFactory:
    @staticmethod
    def get_query(q: SQLQuery, **kwargs):
        if q == SQLQuery.CUMULATIVE_COUNT:
            return f""""
            SELECT 
                output_value,
                COUNT(output_value) AS count,
            FROM
                pipeline_session_output_unit
            WHERE
                created_at >= {kwargs.get("start_time")} AND created_at <= {kwargs.get("end_time")} AND output_key = {kwargs.get("output_key")};
            """
