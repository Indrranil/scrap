-- Create databases
CREATE DATABASE IF NOT EXISTS app_db;
CREATE DATABASE IF NOT EXISTS keycloak_db;

USE app_db;

-- Drop all foreign keys first to avoid constraints issues
SET FOREIGN_KEY_CHECKS = 0;

-- Create tables if they don't exist
CREATE TABLE IF NOT EXISTS `machine` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `mid` varchar(255),
  `name` varchar(255),
  `machine_type` varchar(255),
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE IF NOT EXISTS `property_description` (
  `int` int PRIMARY KEY AUTO_INCREMENT,
  `property_type` ENUM ('machine', 'pipeline', 'application', 'pipeline_input'),
  `description` varchar(255),
  `property_key` varchar(255),
  `property_value_type` varchar(255),
  `property_label` varchar(255),
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE IF NOT EXISTS `general_property` (
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

CREATE TABLE IF NOT EXISTS `application` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255),
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE IF NOT EXISTS `pipeline` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255),
  `is_running` int,
  `application_id` int,
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE IF NOT EXISTS `pipeline_input` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255),
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE IF NOT EXISTS `pipeline_input_referrer` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `key` varchar(255),
  `value` varchar(255),
  `pipeline_input_id` int,
  `created_at` bigint,
  `is_usable` int
);

CREATE TABLE IF NOT EXISTS `pipeline_session` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `pipeline_id` int,
  `pipeline_input_id` int,
  `name` varchar(255),
  `created_by` varchar(255),
  `created_at` bigint,
  `ended_at` bigint,
  `is_usable` int
);

CREATE TABLE IF NOT EXISTS `pipeline_session_output` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `pipeline_session_id` int,
  `name` varchar(255),
  `created_at` bigint,
  `ended_at` bigint,
  `is_usable` int
);

CREATE TABLE IF NOT EXISTS `pipeline_session_output_unit` (
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

CREATE TABLE IF NOT EXISTS `application_container` (
  `id` varchar(255) PRIMARY KEY,
  `application_id` int,
  `created_at` bigint
);

CREATE TABLE IF NOT EXISTS `application_status_log` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `application_container_id` varchar(255),
  `value` ENUM ('start', 'starting', 'started', 'idle', 'running', 'kill', 'killing', 'killed', 'stop', 'stopping', 'stopped', 'error'),
  `created_at` bigint
);

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Create users and grant privileges
CREATE USER IF NOT EXISTS 'app_user'@'%' IDENTIFIED BY 'root';
GRANT ALL PRIVILEGES ON keycloak_db.* TO 'app_user'@'%';
GRANT ALL PRIVILEGES ON app_db.* TO 'app_user'@'%';
FLUSH PRIVILEGES;
