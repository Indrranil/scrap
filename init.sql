CREATE DATABASE IF NOT EXISTS app_db;
USE app_db;

CREATE TABLE `machine` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `mid` varchar(255),
  `name` varchar(255),
  `machine_type` ENUM ('weight_machine', 'perforation', 'rejector'),
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE `property_description` (
  `int` int PRIMARY KEY AUTO_INCREMENT,
  `property_type` ENUM ('machine', 'pipeline', 'application', 'pipeline_input'),
  `description` varchar(255),
  `property_key` varchar(255),
  `property_value_type` varchar(255),
  `property_label` varchar(255),
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE `general_property` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `referrer_id` int COMMENT 'Id of the fact table content such as machine, pipeline, application',
  `property_type` ENUM ('machine', 'pipeline', 'application', 'pipeline_input'),
  `property_label` varchar(255),
  `property_key` varchar(255),
  `property_value` varchar(255),
  `tags` varchar(255) COMMENT 'Can be used to store some additional context',
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE `application` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255),
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE `pipeline` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255),
  `is_running` int,
  `application_id` int,
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

CREATE TABLE `pipeline_session` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `pipeline_id` int,
  `pipeline_input_id` int,
  `name` varchar(255),
  `created_by` varchar(255),
  `created_at` bigint,
  `ended_at` bigint,
  `is_usable` int
);

CREATE TABLE `pipeline_session_output` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `pipeline_session_id` int,
  `name` varchar(255),
  `created_at` bigint,
  `ended_at` bigint,
  `is_usable` int
);

CREATE TABLE `pipeline_session_output_unit` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `pipeline_session_output_id` int,
  `property_reference_id` int,
  `name` varchar(255),
  `output_key` varchar(255),
  `output_value` varchar(255),
  `status` ENUM ('idle', 'ready', 'analysing', 'success', 'error'),
  `verdict` int,
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

ALTER TABLE `pipeline_session` ADD FOREIGN KEY (`pipeline_id`) REFERENCES `application` (`id`);

ALTER TABLE `pipeline_session_output` ADD FOREIGN KEY (`pipeline_session_id`) REFERENCES `pipeline_session` (`id`);

ALTER TABLE `pipeline_session_output_unit` ADD FOREIGN KEY (`pipeline_session_output_id`) REFERENCES `pipeline_session_output` (`id`);

ALTER TABLE `application_container` ADD FOREIGN KEY (`application_id`) REFERENCES `application` (`id`);

ALTER TABLE `pipeline_input_referrer` ADD FOREIGN KEY (`pipeline_input_id`) REFERENCES `pipeline_input` (`id`);

ALTER TABLE `application_status_log` ADD FOREIGN KEY (`application_container_id`) REFERENCES `application_container` (`id`);

ALTER TABLE `pipeline_session_output_unit` ADD FOREIGN KEY (`property_reference_id`) REFERENCES `general_property` (`id`);


CREATE DATABASE IF NOT EXISTS keycloak_db;
USE keycloak_db;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON keycloak_db.* TO 'app_user'@'%';
FLUSH PRIVILEGES;
