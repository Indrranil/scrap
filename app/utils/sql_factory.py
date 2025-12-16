import enum


class SQLQuery(enum.Enum):
    CUMULATIVE_COUNT = "cumulative_count"
    RAW_OUTPUT = "raw_output"


class SQLFactory:
    @staticmethod
    def get_query(q: SQLQuery, **kwargs):
        if q == SQLQuery.CUMULATIVE_COUNT:
            return f"""
            SELECT 
                output_value,
                COUNT(output_value) AS count
            FROM
                pipeline_session_output_unit
            WHERE
                created_at >= {kwargs.get("start_time")} AND created_at <= {kwargs.get("end_time")} AND output_key = '{kwargs.get("output_key")}'
            GROUP BY 
                output_value;
            """

        elif q == SQLQuery.RAW_OUTPUT:
            return f"""
            SELECT 
                psou.*
            FROM
                pipeline_session_output_unit psou
            JOIN
                pipeline_session_output pso ON pso.id = psou.pipeline_session_output_id
            JOIN
                pipeline_session ps ON ps.id = pso.pipeline_session_id AND ps.pipeline_id = {kwargs.get("pipeline_id")}
            WHERE
                psou.created_at >= {kwargs.get("start_time")} AND psou.created_at <= {kwargs.get("end_time")};
            """

        return None
