# HUL App Schema - v1
A generalized schema designed to accomodate various kinds of data involved in the PolarisAI application stack in a simplified way.

## Tables

1) Machine

    Any kind of device such as *server, rejector, weight machine, perforation machine* can be registered in this table.
    ```sql
    CREATE TABLE `machine` (
      `id` int PRIMARY KEY AUTO_INCREMENT,
      `mid` varchar(255),
      `name` varchar(255),
      `machine_type` ENUM ('camera', 'server', 'rejector'),
      `created_at` bigint,
      `is_usable` int
    );
    ```
    > Note: `mid` is a unique identifier which is derived from a standard naming convention 
    
    Sample:

    | id | mid | machine_type | name               | created_at    | is_usable |
    |----|-----|--------------|--------------------|---------------|-----------|
    | 1  | R1  | rejector     | Line 1 rejector    | 1736705992000 | 1         |
    | 2  | P1  | perforation  | Line 1 perforation | 1736705992000 | 1         |
    | 3  | R2  | rejector     | Line 2 rejector    | 1736705992000 | 1         |

2) Property Description

    This table essentially holds all the type of *properties* an entity can possibly hold but not limited to.
    ```sql
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
    ```
    Sample:

    | id | property_type  | description          | property_key  | property_value_type | property_label | created_at    | is_usable |
    |----|----------------|----------------------|---------------|---------------------|----------------|---------------|-----------|
    | 1  | machine        | IP address           | ip_address    | string              | IP Address     | 1736705992000 | 1         |
    | 2  | application    | Detector model path  | detector_path | string              | Detector Path  | 1736705992000 | 1         |
    | 3  | pipeline_input | Price of the product | coding        | string              | Price          | 1736705992000 | 1         |
    | 4  | pipeline_input | Front code           | material_code | string              | Front          | 1736705992000 | 1         |

3) General Property

    This table holds all the properties of different entities such as *machine, application, pipeline & pipeline input*
    ```sql
    CREATE TABLE `general_property` (
      `id` int PRIMARY KEY AUTO_INCREMENT,
      `referrer_id` int COMMENT 'Id of the fact table content such as machine, pipeline, application',
      `property_type` ENUM ('machine', 'pipeline', 'application', 'pipeline_input'),
      `property_label` varchar(255),
      `property_key` varchar(255),
      `property_value` varchar(255),
      `created_at` bigint,
      `is_usable` int
    );
    ```
   Sample:

   | id | referrer_id | property_type  | property_key  | property_value | property_label | created_at    | is_usable |
    |----|-------------|----------------|---------------|----------------|----------------|---------------|-----------|
    | 1  | 1           | machine        | ip_address    | 127.0.0.1      | IP Address     | 1736705992000 | 1         |
    | 2  | 1           | pipeline_input | perforation   | NULL           | min            | 1736705992000 | 1         |
    | 3  | 1           | pipeline_input | target_weight | 102.44         | Weight         | 1736705992000 | 1         |
    > Note: When a property is used as a reference value and the value is `NULL`, the property is not used for comparison unlike most cases

4) Application

   An application is defined as any specific use case *cv application* such as *party_pack_rejection*, *qc_pipeline*. These applications are registered here.
   ```sql
    CREATE TABLE `application` (
      `id` int PRIMARY KEY AUTO_INCREMENT,
      `name` varchar(255),
      `created_at` bigint,
      `is_usable` int
    );
    ```
    > Note: This table can be extended to any application such as rejector, perforation reader etc. [upcoming]
    
    Sample:

    | id | name                 | created_at    | is_usable |
    |----|----------------------|---------------|-----------|
    | 1  | Party Pack Rejection | 1736705992000 | 1         |
    | 2  | QC Pipeline          | 1736705992000 | 1         |
    | 3  | Sticker QR           | 1736705992000 | 1         |
    
5) Pipeline

    A pipeline is derived from an *application* where the same application is running in muliple places with different `input` such as *tub_count_110 & tub_count_111*
    ```sql
    CREATE TABLE `pipeline` (
      `id` int PRIMARY KEY AUTO_INCREMENT,
      `name` varchar(255),
      `is_running` int,
      `pipeline_id` int,
      `created_at` bigint,
      `is_usable` int
    );
    ```
    Sample:

    | id | name                    | is_running | pipeline_id | created_at    | is_usable |
    |----|-------------------------|------------|-------------|---------------|-----------|
    | 1  | Tub Count - Line 3      | 1          | 1           | 1736705992000 | 1         |
    | 2  | Tub Count - Line 4      | 0          | 1           | 1736705992000 | 1         |
    | 3  | QC Pipeline - Factory 3 | 1          | 2           | 1736705992000 | 1         |
    
6) Pipeline Input

   As the name says, this table holds the available inputs for the pipelines which are used as reference values.
   ```sql
   CREATE TABLE `pipeline_input` (
      `id` int PRIMARY KEY AUTO_INCREMENT,
      `name` varchar(255),
      `created_at` bigint,
      `is_usable` int
    );
   ```
   Sample:

   | id | name                                | created_at    | is_usable |
    |----|-------------------------------------|---------------|-----------|
    | 1  | DOVE DS BIO 340 ml                  | 1736705992000 | 1         |
    | 2  | CLINIC PLUS STRONG&LONG SHMP 175 ML | 1736705992000 | 1         |
    | 3  | Jam Jar Pack - 30 Count             | 1736705992000 | 1         |

7) Pipeline Input Referrer

   This table contains properties which have direct reference to *pipeline inputs* such as *CLD Barcode*. This is useful in situations where we have to choose a *pipeline input* dynamically based off some value.
   ```sql
   CREATE TABLE `pipeline_input_referrer` (
      `id` int PRIMARY KEY AUTO_INCREMENT,
      `key` varchar(255),
      `value` varchar(255),
      `pipeline_input_id` int,
      `created_at` bigint,
      `is_usable` int
    );
   ```
   > Note: we cannot add CLD Barcode as one of the properties of pipeline input because it is not used as a reference value 
   
   Sample:

   | id | key         | value       | pipeline_input_id | created_at    | is_usable |
    |----|-------------|-------------|-------------------|---------------|-----------|
    | 1  | cld_barcode | 18368963304 | 1                 | 1736705992000 | 1         |
    | 2  | rfid        | 18368963305 | 2                 | 1736705992000 | 1         |
    | 3  | qr_code     | 18368963306 | 3                 | 1736705992000 | 1         |
8) Pipeline Session

   When a pipeline is started, a record is added to this table indicating a session.
   ```sql
   CREATE TABLE `pipeline_session` (
      `id` int PRIMARY KEY AUTO_INCREMENT,
      `application_id` int,
      `name` varchar(255),
      `created_by` int,
      `created_at` bigint,
      `ended_at` bigint,
      `is_usable` int
    );
   ```
   Sample:

   | id | pipeline_id | name | created_by  | created_at    | ended_at      | is_usable |
    |----|-------------|------|-------------|---------------|---------------|-----------|
    | 1  | 1           | Auto | quality_ddf | 1736705992000 | 1736705992000 | 1         |
    | 2  | 2           | NULL | admin       | 1736705992000 | NULL          | 1         |
    | 3  | 1           | Auto | quality_ddf | 1736705992000 | NULL          | 1         |

9) Pipeline Session Output

   A *pipeline session* output is a single payload that comes from the pipeline as the output, usually the result of *OCR*. Each of this output is recorded in this table.
   ```sql
   CREATE TABLE `pipeline_session_output` (
      `id` int PRIMARY KEY AUTO_INCREMENT,
      `pipeline_session_id` int,
      `name` varchar(255),
      `created_at` bigint,
      `ended_at` bigint,
      `is_usable` int
    );
   ```
   Sample:

   | id | pipeline_session_id | name | created_at    | ended_at | is_usable |
    |----|---------------------|------|---------------|----------|-----------|
    | 1  | 1                   | NULL | 1736705992000 | NULL     | 1         |
    | 2  | 2                   | NULL | 1736705992000 | NULL     | 1         |
    | 3  | 1                   | NULL | 1736705992000 | NULL     | 1         |

10) Pipeline Session Output Unit

    A *pipeline session output unit* refers to a single *key-value* pair in the output payload that comes from the pipeline. Each unit corresponds to a *pipeline input property*.
    *status* matters only in the case of manual pipeline sessions.
    ```sql
    CREATE TABLE `application_session_output_unit` (
      `id` int PRIMARY KEY AUTO_INCREMENT,
      `pipeline_session_output_id` int,
      `reference_id` int, -- reference to general_property 
      `name` varchar(255),
      `output_key` varchar(255),
      `output_value` varchar(255),
      `status` ENUM ('idle', 'ready', 'analysing', 'success', 'error'),
      `created_at` bigint,
      `is_usable` int
    );
    ```
    Process flow:
       ```text
       .
        └── pipeline session/
            ├── pipeline session output 1/
            │   ├── pipeline session output unit 1
            │   ├── pipeline session output unit 2
            │   ├── pipeline session output unit 3
            │   └── pipeline session output unit 4
            ├── pipeline session output 2/
            │   ├── pipeline session output unit 1
            │   ├── pipeline session output unit 2
            │   ├── pipeline session output unit 3
            │   └── pipeline session output unit 4
            └── pipeline session output 3/
                ├── pipeline session output unit 1
                ├── pipeline session output unit 2
                ├── pipeline session output unit 3
                └── pipeline session output unit 4
       ```
    
    Sample:

    | id | pipeline_session_output_id | reference_id | output_key          | output_value | created_at    | is_usable |
    |----|----------------------------|--------------|---------------------|--------------|---------------|-----------|
    | 1  | 1                          | 1            | price               | 220/-        | 1736705992000 | 1         |
    | 2  | 1                          | 2            | front_material_code | 38473294290  | 1736705994000 | 1         |
    | 3  | 1                          | 3            | barcode             | 13823478     | 1736705995000 | 1         |

11) Pipeline Container

    When a pipeline is started *using a docker container or as a subprocess*, a record is added to this table which will be used for *monitoring purposes*.
    ```sql
    CREATE TABLE `pipeline_container` (
      `id` varchar(255) PRIMARY KEY,
      `pipeline_id` int,
      `created_at` bigint
    );
    ```
    Sample:

    | id | pipeline_id | created_at    |
    |----|-------------|---------------|
    | 1  | 1           | 1736705992000 |
    | 2  | 2           | 1736705992000 |
    | 3  | 1           | 1736705992000 |

12) Pipeline Status Log

    This table is used to store the *run status* of *pipeline container*.
    ```sql
    CREATE TABLE `pipeline_status_log` (
      `id` int PRIMARY KEY AUTO_INCREMENT,
      `pipeline_container_id` varchar(255),
      `value` ENUM ('start', 'starting', 'started', 'idle', 'running', 'kill', 'killing', 'killed', 'stop', 'stopping', 'stopped', 'error'),
      `created_at` bigint
    );
    ```
    Sample:

    | id | pipeline_container_id | value    | created_at    |
    |----|-----------------------|----------|---------------|
    | 1  | 1                     | start    | 1736705992000 |
    | 2  | 1                     | starting | 1736705992000 |
    | 3  | 1                     | started  | 1736705992000 |
    | 4  | 1                     | idle     | 1736705992000 |
    | 5  | 1                     | running  | 1736705992000 |
    | 6  | 1                     | kill     | 1736705992000 |
    
    > Use case: A container/subprocess is restarted if it's `idle` for more than `x` seconds. `idle` state indicates that the frames are not being processed.

