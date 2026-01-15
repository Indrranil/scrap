-- Query to fetch session data shift & operator wise

SELECT
    DATE(FROM_UNIXTIME(ps.created_at)) AS session_date,
    ps.name,
    gp.property_value AS status,
    gp1.property_value created_by,
    CASE
        WHEN TIME(FROM_UNIXTIME(ps.created_at)) >= '06:00:00' AND TIME(FROM_UNIXTIME(ps.created_at)) < '14:00:00'
            THEN 'A'
        WHEN TIME(FROM_UNIXTIME(ps.created_at)) >= '14:00:00' AND TIME(FROM_UNIXTIME(ps.created_at)) < '22:00:00'
            THEN 'B'
        ELSE 'C'
    END AS shift,
    COUNT(*) AS total_sessions
FROM pipeline_session ps
JOIN general_property gp ON gp.referrer_id = ps.id AND gp.property_type = "pipeline_session"  AND gp.property_key = "status" AND gp.property_value = "submitted"
JOIN general_property gp1 ON gp1.referrer_id = ps.id AND gp1.property_type = "pipeline_session"  AND gp1.property_key = "created_by"
WHERE ps.created_at >= UNIX_TIMESTAMP(NOW() - INTERVAL 10 DAY) and ps.name in ("startup_session", "changeover_session", "pcro_session")
GROUP BY ps.name, session_date, gp1.property_value, shift
ORDER BY session_date DESC, shift;
