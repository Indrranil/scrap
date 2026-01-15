-- Procedure to automatically update Manufacturing Date for all products monthly
-- This is the new schema version for general_property table

DELIMITER //
CREATE PROCEDURE update_tube_manufacturing_date()
BEGIN
  DECLARE current_month VARCHAR(5);
  SET current_month = DATE_FORMAT(NOW(), '%m/%y');

  -- Insert new Manufacturing Date properties for all pipeline_input records
  -- that have existing Manufacturing Date properties
  INSERT INTO general_property (referrer_id, property_type, property_key, property_label, property_value, created_at, is_usable)
  SELECT 
    gp.referrer_id,
    'pipeline_input' as property_type,
    'tube_coding' as property_key,
    'Manufacturing Date' as property_label,
    current_month as property_value,
    UNIX_TIMESTAMP() as created_at,
    1 as is_usable
  FROM (
    SELECT referrer_id, MAX(id) AS latest_id
    FROM general_property
    WHERE property_type = 'pipeline_input' 
    AND property_label = 'Manufacturing Date'
    AND property_key = 'coding'
    AND is_usable = 1
    GROUP BY referrer_id
  ) AS latest_rows
  JOIN general_property gp
  ON latest_rows.referrer_id = gp.referrer_id
  AND latest_rows.latest_id = gp.id
  AND gp.property_type = 'pipeline_input'
  AND gp.property_label = 'Manufacturing Date'
  AND gp.is_usable = 1;

END //
DELIMITER ;
