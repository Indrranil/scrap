-- Event scheduler to automatically run Manufacturing Date update monthly
-- This is the new schema version for general_property table

CREATE EVENT update_tube_manufacturing_date_event
ON SCHEDULE EVERY 1 MONTH
STARTS '2025-09-01 01:30:00'
DO
  CALL update_tube_manufacturing_date();
