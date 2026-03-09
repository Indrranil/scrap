import enum


class SQLQuery(enum.Enum):
    CUMULATIVE_COUNT = "cumulative_count"
    RAW_OUTPUT = "raw_output"
    OUTPUT_BY_VALUE = "output_by_value"
    CUMULATIVE_VALUE = "cumulative_value"


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

        elif q == SQLQuery.OUTPUT_BY_VALUE:
            return f"""
            WITH results AS (
                SELECT DISTINCT(pso.id) AS id
                FROM pipeline_session ps
                JOIN pipeline_session_output pso ON ps.id = pso.pipeline_session_id
                JOIN pipeline_session_output_unit psou ON pso.id = psou.pipeline_session_output_id and psou.output_key = "{kwargs.get("output_key")}" and psou.output_value = "{kwargs.get("output_value")}"
            )
            SELECT 
                psou.*
            FROM
                pipeline_session_output_unit psou
            JOIN
                results r
            JOIN
                pipeline_session_output pso ON pso.id = psou.pipeline_session_output_id AND r.id =pso.id
            JOIN
                pipeline_session ps ON ps.id = pso.pipeline_session_id
            ORDER BY
                psou.id DESC
            LIMIT
                {kwargs.get('limit')}
            OFFSET
                {kwargs.get('offset')};
            """

        elif q == SQLQuery.CUMULATIVE_VALUE:
            return f"""
            SELECT 
                SUM(CAST(REPLACE(psou.output_value, '{kwargs.get("suffix")}', '') AS DECIMAL(10,3))) AS cumulative_value
            FROM
                pipeline_session_output_unit psou
            JOIN
                pipeline_session_output pso ON pso.id = psou.pipeline_session_output_id
            JOIN
                pipeline_session ps ON ps.id = pso.pipeline_session_id AND ps.pipeline_id = {kwargs.get("pipeline_id")}
            WHERE
                psou.created_at >= {kwargs.get("start_time")} AND psou.created_at <= {kwargs.get("end_time")} AND psou.output_key = '{kwargs.get("output_key")}';
            """

        return None


f"""
SELECT 
                SUM(CAST(REPLACE(psou.output_value, 'kg', '') AS DECIMAL(10,3))) AS cumulative_value
            FROM
                pipeline_session_output_unit psou
            JOIN
                pipeline_session_output pso ON pso.id = psou.pipeline_session_output_id
            JOIN
                pipeline_session ps ON ps.id = pso.pipeline_session_id AND ps.pipeline_id = 4
            WHERE
                psou.created_at >= 0 AND psou.created_at <= 1773054714 AND psou.output_key = 'weight';
"""
