CREATE DATABASE IF NOT EXISTS app_db;
USE app_db;

CREATE TABLE `machine` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `mid` varchar(255),
  `factory_id` varchar(255),
  `plant_id` varchar(255),
  `location` varchar(255),
  `machine_type` ENUM ('camera', 'server', 'rejector'),
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE `general_property` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `referrer_id` int COMMENT 'Id of the fact table content such as machine, pipeline, application',
  `property_type` ENUM ('machine', 'pipeline', 'application', 'pipeline_input'),
  `property_key` varchar(255),
  `property_value` varchar(255),
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE `pipeline` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255),
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE `application` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255),
  `is_running` int,
  `pipeline_id` int,
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE `pipeline_input` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255),
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE `pipeline_input_referrer` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `key` varchar(255),
  `value` varchar(255),
  `pipeline_input_id` int,
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE `application_session` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `application_id` int,
  `name` varchar(255),
  `created_by` int,
  `created_at` bigint,
  `ended_at` bigint,
  `is_usable` int
);

CREATE TABLE `application_session_unit` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `application_session_id` int,
  `name` varchar(255),
  `created_at` bigint,
  `ended_at` bigint,
  `is_usable` int
);

CREATE TABLE `application_session_unit_output` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `application_session_unit_id` int,
  `name` varchar(255),
  `output_key` varchar(255),
  `output_value` varchar(255),
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE `application_container` (
  `id` varchar(255) PRIMARY KEY,
  `application_id` int,
  `created_at` bigint
);

CREATE TABLE `application_status_log` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `application_container_id` varchar(255),
  `value` ENUM ('start', 'starting', 'started', 'idle', 'running', 'kill', 'killing', 'killed', 'stop', 'stopping', 'stopped', 'error'),
  `created_at` bigint
);

CREATE TABLE `application_output_type` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `application_id` int,
  `key_name` varchar(255),
  `is_usable` int,
  `created_at` bigint
);

ALTER TABLE `general_property` ADD FOREIGN KEY (`referrer_id`) REFERENCES `machine` (`id`);

ALTER TABLE `general_property` ADD FOREIGN KEY (`referrer_id`) REFERENCES `pipeline` (`id`);

ALTER TABLE `general_property` ADD FOREIGN KEY (`referrer_id`) REFERENCES `application` (`id`);

ALTER TABLE `general_property` ADD FOREIGN KEY (`referrer_id`) REFERENCES `pipeline_input` (`id`);

ALTER TABLE `application_session` ADD FOREIGN KEY (`application_id`) REFERENCES `application` (`id`);

ALTER TABLE `application_session_unit` ADD FOREIGN KEY (`application_session_id`) REFERENCES `application_session` (`id`);

ALTER TABLE `application_session_unit_output` ADD FOREIGN KEY (`application_session_unit_id`) REFERENCES `application_session_unit` (`id`);

ALTER TABLE `application_container` ADD FOREIGN KEY (`application_id`) REFERENCES `application` (`id`);

ALTER TABLE `pipeline_input_referrer` ADD FOREIGN KEY (`pipeline_input_id`) REFERENCES `pipeline_input` (`id`);

ALTER TABLE `application_status_log` ADD FOREIGN KEY (`application_container_id`) REFERENCES `application_container` (`id`);

ALTER TABLE `application_output_type` ADD FOREIGN KEY (`application_id`) REFERENCES `application` (`id`);


CREATE DATABASE IF NOT EXISTS keycloak_db;
USE keycloak_db;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON keycloak_db.* TO 'app_user'@'%';
FLUSH PRIVILEGES;
