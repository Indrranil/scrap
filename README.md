# PolarisAI Backend

Backend services for PolarisAI using FastAPI, MySQL, and Keycloak.

## Prerequisites
- Docker
- Docker Compose

## Creating SSL certificate for keycloak
1. **create** keycloak folder. inside this folder **create** another folder as certs
2. ```bash
      keytool -genkeypair -alias keycloak \
      -keyalg RSA -keysize 2048 \
      -validity 365 -keystore keycloak/certs/keystore.p12 \
      -storetype PKCS12 \
      -dname "CN=localhost, OU=Development, O=MyOrg, L=MyCity, S=MyState, C=IN" \
      -storepass your-keystore-password -keypass your-key-password
   ```
   Change this variable according to you needs.
   **NOTE** remember your store pass, we will need to setup the variable in env.sh script.
3. Mount your the folder inside the docker-compose file under keycloak volume. You need to set the relative path to certificate in env.sh file
The variable name will be like this ```KEYCLOAK_SSL_CERT=../keycloak/certs/keystore.p12```
4. Set this variable in env.sh file ``` KC_HTTPS_KEY_STORE_PASSWORD=rootpass```
5. ensure this setting ```KC_HOSTNAME_STRICT_HTTPS`` is true to ensure it runs only on https in docker compose file.
6. set port 8443 for https and 8080 for http in env.sh script 

## Setup

1. Clone the repository
    ```bash
    git clone -b dev https://github.com/prowiz-analytics/polarisai-app-api
    ```

2. Create `env.sh` file in the root directory
    ```env.sh
  export API_PORT=8000
  export MYSQL_ROOT_PASSWORD=rootpass
  export MYSQL_DATABASE=app_db
  export MYSQL_USER=app_user
  export MYSQL_PASSWORD=root
  export MYSQL_HOST_PORT=3308
  export MYSQL_PORT=3306
  export KC_DB_USERNAME=root
  export KC_DB_PASSWORD=rootpass
  export KEYCLOAK_ADMIN_PASSWORD=admin_password
  export KC_HTTPS_KEY_STORE_PASSWORD=rootpass
  export KEYCLOAK_HTTP_PORT=8080  
  export KEYCLOAK_HTTPS_PORT=8443
  export KEYCLOAK_SSL_CERT=../keycloak/certs/keystore.p12
  ```

3. Run the env.sh file 
  ```bash
    cd build_infra
    source ../env.sh
    ```

4. Run the API
    ```bash
    docker-compose up -d
    ```
## Keycloak Setup

After the services are running, you need to configure Keycloak:

1. **Create Realm**: Go to http://localhost:8080,or https://localhost:8443 if using SSL certificate. create a realm named "app-realm" & select it
2. **Create Client**: Create a client named "api", enable all authentication & authorization flows. Select the created client, choose "credentials", copy client secret (for API env)
3. **Create User**: Create a user with username "tester", email "tester@email.com", enter both first and last name, mark email as verified
4. **Set Password**: Create a password for that user, uncheck temporary password
5. **Create Role**: Create a realm role named "app_admin", link it with the user

After setup, you can access the API using the test user.

## Access Points

### Service URLs
- FastAPI: http://localhost:8000
- Keycloak: http://localhost:8080 / https://localhost:8443
- MySQL: localhost:3308

## Docker Operations

### Container Management
```bash
# View MySQL logs
docker-compose logs -f mysql

# Stop all services
docker-compose down
```

### Database Operations
```bash
# Backup database
docker exec mysql-docker-mysql-1 mysqldump -u root -prootpass app_db > app_db_backup.sql

# Restore database
docker cp app_db_backup.sql mysql-docker-mysql-1:/tmp/app_db_backup.sql
docker exec -it mysql-docker-mysql-1 mysql -u root -prootpass

# In MySQL prompt
use app_db;
source /tmp/app_db_backup.sql;
```

## Database Access
```bash
# Connect to MySQL
docker exec -it mysql-docker-mysql-1 mysql -u app_user -p
# Password: root
```

# Architecture

## Overview
> The PolarisAI backend is designed to manage data processing workflows, leveraging FastAPI for API development, MySQL for database management, and Keycloak for authentication. This repository contains all necessary components to set up and run the backend services.

## Components
> - **FastAPI:** Handles API endpoints for managing machines, pipeline inputs, sessions, outputs, and insights.  
> - **MySQL:** Stores data related to applications, machines, pipeline inputs/outputs.  
> - **Keycloak:** Manages user authentication through secure token-based access.

## Functionality
> This backend supports various functionalities:
> - **Machine Management:** Registering new devices (machines) that can be used in pipelines.
> - **Pipeline Input Management:** Creating new inputs that are processed by pipelines.
> - **Pipeline Session Management:** Initiating sessions where data is processed through pipelines.
> - **Output Management:** Handling results from pipeline sessions (outputs).
> - **Insight Retrieval:** Providing analytical views based on session attributes or verdicts.

## Project Structure
> - **`app/`**: Main application directory containing source code.
>     - **`auth/`**: Authentication-related code (e.g., RBAC, authentication logic).
>     - **`config/`**: Configuration files for the application (e.g., permissions).
>     - **`database/`**: Database connection logic (e.g., connection setup).
>     - **`main.py`**: Entry point for the FastAPI application.
>     - **`models/`**: Data models representing database tables (e.g., Application, Machine).
>     - **`requirements.txt`**: Lists Python dependencies.
>     - **`routers/`**: Defines API endpoints for different functionalities (e.g., Machine management, Pipeline input management).
>     - **`schemas/`**: Defines Pydantic schemas for request/response data validation.
>     - **`tests/`**: Contains unit tests.
> - **`build_infra/`**: Docker infrastructure files.
> - **`keycloak/`**: Configuration files related to Keycloak (e.g., realm setup).

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

# HUL API - v1

[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)

A generalized API which can be used by multiple specific use-case applications.

## Features

- Role based access control (RBAC)
- File based data upload
- Optimized data writing avoiding duplicate instances

## Routers

### 1) Authentication Endpoints

   * #### Authenticate User
       <details>
         <summary><code>POST</code> <code><b>/v1/auth/signin</b></code> <code>(authenticate user)</code></summary>
        
        ##### Description
        > This endpoint is used to authenticate a user. It validates the provided credentials and forwards the request to Keycloak. Upon successful authentication, the endpoint returns an access token along with additional token details.

        ##### URL & Method
        > **URL:** `/v1/auth/signin`  
        > **Method:** `POST`

        ##### Request Payload
        > The request body must match the following JSON schema:
        > 
        > ```json
        > {
        >   "username": "string",
        >   "password": "string"
        > }
        > ```

        ##### Validation
        > - Both username and password are required and must not be empty.
        > - Pydantic validators ensure that any empty or whitespace-only values are rejected.

        ##### Processing Details
        > - Reads the Keycloak configuration (URL, realm, client ID, and client secret) from environment variables.
        > - Sends a POST request to Keycloak’s token endpoint with the provided credentials.
        > - Handles possible error scenarios such as missing configuration, connection issues, server errors from Keycloak, or invalid credentials.

        ##### Response
        > On success, a JSON response similar to the following is returned:
        > 
        > ```json
        > {
        >   "access_token": "string",
        >   "token_type": "string",
        >   "expires_in": 3600,
        >   "refresh_token": "string"
        > }
        > ```

        ##### Error Responses
        > **401 Unauthorized:**  
        > - Returned if the Keycloak URL is not configured.  
        > - Returned if Keycloak responds with an error (e.g., server error or invalid credentials).
        >
        > **422 Unprocessable Entity:**  
        > - Returned if input validation fails (e.g., empty username or password).
        
       </details>

### 2) Application Endpoints

   * #### Create New Application
       <details>
         <summary><code>POST</code> <code><b>/v1/application/</b></code> <code>(creates a new application)</code></summary>
        
        ##### Description
        > This endpoint creates a new application. It checks for duplicate application names before creation and records the creation timestamp.
        
        ##### URL & Method
        > **URL:** `/v1/application/`  
        > **Method:** `POST`
        
        ##### Request Payload
        > The request body should match the `ApplicationCreate` schema:
        > 
        > ```json
        > {
        >   "name": "string",
        >   "is_usable": 1
        > }
        > ```
        > - **name:** The name of the application. Must not be empty and cannot exceed 255 characters.
        > - **is_usable:** (Optional) Integer flag indicating usability. Default is `1`.
        
        ##### Processing Details
        > - Logs the creation attempt with the provided data.
        > - Checks for duplicate application name using `check_duplicate_name`. If a duplicate exists, responds with a 400 error.
        > - Creates a new application record with the current timestamp (`created_at`) and saves it to the database.
        
        ##### Responses
        > - **201 Created:**  
        >   - Returns the newly created application details including `id`, `name`, `created_at`, and `is_usable`.
        
        ##### Error Responses
        > - **400 Bad Request:**  
        >   - If an application with the provided name already exists.
        > - **500 Internal Server Error:**  
        >   - If an error occurs during the creation process.
        
       </details>

   * #### Get All Applications
       <details>
         <summary><code>GET</code> <code><b>/v1/application/all</b></code> <code>(retrieves all usable applications)</code></summary>
        
        ##### Description
        > Retrieves a list of all applications that are marked as usable (`is_usable` equals `1`).
        
        ##### URL & Method
        > **URL:** `/v1/application/all`  
        > **Method:** `GET`
        
        ##### Processing Details
        > - Queries the database for applications where `is_usable` is `1`.
        
        ##### Responses
        > - **200 OK:**  
        >   - Returns a list of application objects.
        
        ##### Example cURL
        > ```bash
        > curl -X GET -H "Content-Type: application/json" http://localhost:8000/v1/application/all
        > ```
        
       </details>

   * #### Get Application by ID
       <details>
         <summary><code>GET</code> <code><b>/v1/application/{application_id}</b></code> <code>(retrieves a specific application)</code></summary>
        
        ##### Description
        > Retrieves details of a specific application identified by its ID.
        
        ##### URL & Method
        > **URL:** `/v1/application/{application_id}`  
        > **Method:** `GET`
        
        ##### Path Parameters
        > | Parameter         | Type  | Description                         |
        > |-------------------|-------|-------------------------------------|
        > | `application_id`  | int   | Unique ID of the application.       |
        
        ##### Responses
        > - **200 OK:**  
        >   - Returns the application object.
        > - **404 Not Found:**  
        >   - If the application with the specified ID does not exist or is not usable.
        
        ##### Example cURL
        > ```bash
        > curl -X GET -H "Content-Type: application/json" http://localhost:8000/v1/application/1
        > ```
        
       </details>

   * #### Update Application
       <details>
         <summary><code>PATCH</code> <code><b>/v1/application/{application_id}</b></code> <code>(updates an existing application)</code></summary>
        
        ##### Description
        > Updates the details of an existing application identified by its ID. Also checks for duplicate names when updating.
        
        ##### URL & Method
        > **URL:** `/v1/application/{application_id}`  
        > **Method:** `PATCH`
        
        ##### Path Parameters
        > | Parameter         | Type  | Description                         |
        > |-------------------|-------|-------------------------------------|
        > | `application_id`  | int   | Unique ID of the application.       |
        
        ##### Request Payload
        > The request body should conform to the `ApplicationCreate` schema:
        > 
        > ```json
        > {
        >   "name": "string",
        >   "is_usable": 1
        > }
        > ```
        > - **name:** New name for the application.
        > - **is_usable:** Usability flag.
        
        ##### Processing Details
        > - Checks if the application exists and is marked as usable.
        > - Validates the new name to ensure no duplicate exists (excluding the current application).
        > - Updates the application's `name` and `is_usable` status in the database.
        
        ##### Responses
        > - **200 OK:**  
        >   - Returns the updated application object.
        > - **400 Bad Request:**  
        >   - If the new name already exists for another application.
        > - **404 Not Found:**  
        >   - If the application with the specified ID is not found.
        > - **500 Internal Server Error:**  
        >   - If an error occurs during the update process.
        
        ##### Example cURL
        > ```bash
        > curl -X PATCH -H "Content-Type: application/json" -d '{"name": "New App Name", "is_usable": 1}' http://localhost:8000/v1/application/1
        > ```
        
       </details>

   * #### Delete Application
       <details>
         <summary><code>DELETE</code> <code><b>/v1/application/{application_id}</b></code> <code>(deletes an application)</code></summary>
        
        ##### Description
        > Soft deletes an application by setting its `is_usable` flag to `0`.
        
        ##### URL & Method
        > **URL:** `/v1/application/{application_id}`  
        > **Method:** `DELETE`
        
        ##### Path Parameters
        > | Parameter         | Type  | Description                         |
        > |-------------------|-------|-------------------------------------|
        > | `application_id`  | int   | Unique ID of the application.       |
        
        ##### Processing Details
        > - Checks if the application exists and is usable.
        > - Performs a soft delete by setting the `is_usable` flag to `0`.
        > - Commits the change to the database.
        
        ##### Responses
        > - **200 OK:**  
        >   - Returns a success message confirming deletion.
        > - **404 Not Found:**  
        >   - If the application with the specified ID is not found.
        > - **500 Internal Server Error:**  
        >   - If an error occurs during deletion.
        
        ##### Example cURL
        > ```bash
        > curl -X DELETE -H "Content-Type: application/json" http://localhost:8000/v1/application/1
        > ```
        
       </details>

### 3) Machine
    
   * #### Creating new machines
       <details>
         <summary><code>POST</code> <code><b>/machine/new</b></code> <code>(creates new machine/machines)</code></summary>
        
       ##### Supported machine types
        > | S.No | Machine Type   |
        > |------|----------------|
        > | 1    | Rejector       |        
        > | 2    | Perforation    | 
        > | 3    | Weight Machine | 

        ##### Payload
        > | name           | type     | data type | description            |
        > |----------------|----------|-----------|------------------------|
        > | `name`         | required | string    | The machine name       |
        > | `machine_type` | required | string    | Supported machine type |
        > | `mid`          | optional | string    | Machine ID             |
        
        ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `201`     | `application/json;charset=UTF-8` | {}       |
        > | `400`     | `application/json;charset=UTF-8` | {}       |
        > | `500`     | `application/json;charset=UTF-8` | {}       |
   
        ##### Example cURL
        
        > ```bash
        >  curl -X POST -H "Content-Type: application/json" http://localhost:8000/api/v1/machine/new
        > ```
        
        </details>
        
        <details>
         <summary><code>POST</code> <code><b>/machine/new/upload</b></code> <code>(creates new machines from uploaded csv)</code></summary>
        
        ##### Payload
        > | name   | type     | data type      | description              |
        > |--------|----------|----------------|--------------------------|
        > | `file` | required | form/multipart | CSV file containing data |
        
        ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `201`     | `application/json;charset=UTF-8` | {}       |
        > | `400`     | `application/json;charset=UTF-8` | {}       |
        > | `500`     | `application/json;charset=UTF-8` | {}       |
        
        ##### Example cURL
        
        > ```bash
        >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/machine/all
        > ```
        
        </details>
        

   * #### Listing existing machines
       <details>
         <summary><code>GET</code> <code><b>/machine/{id}</b></code> <code>(gets a machine by id)</code></summary>
        
        ##### Parameters
        > | name |  type     | data type      | description    |
        > |------|-----------|----------------|----------------|
        > | `id` |  required | int ($int64)   | The machine id |
        
        ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `200`     | `application/json;charset=UTF-8` | payload  |
        
        ##### Example cURL
        
        > ```bash
        >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/machine/1
        > ```
        
        </details>
        
        <details>
         <summary><code>GET</code> <code><b>/machine/all</b></code> <code>(gets all machines)</code></summary>
        
        ##### Parameters
        > None
        
        ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `200`     | `application/json;charset=UTF-8` | payload  |
        
        ##### Example cURL
        
        > ```bash
        >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/machine/all
        > ```
        
        </details>


### 4) Pipeline Input
    
* #### Creating new pipeline input
    <details>
      <summary><code>POST</code> <code><b>/pipeline-input/new</b></code> <code>(creates new pipeline input/s)</code></summary>
        
  ##### Payload
        > | name           | type     | data type | description            |
        > |----------------|----------|-----------|------------------------|
        > | `name`         | required | string    | The machine name       |
        > | `machine_type` | required | string    | Supported machine type |
        > | `mid`          | optional | string    | Machine ID             |
        
     ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `201`     | `application/json;charset=UTF-8` | {}       |
        > | `400`     | `application/json;charset=UTF-8` | {}       |
        > | `500`     | `application/json;charset=UTF-8` | {}       |
   
     ##### Example cURL
        
        > ```bash
        >  curl -X POST -H "Content-Type: application/json" http://localhost:8000/api/v1/pipeline-input/new
        > ```
        
     </details>
        
     <details>
      <summary><code>POST</code> <code><b>/pipeline-input/new/upload</b></code> <code>(creates new pipeline inputs from uploaded csv)</code></summary>
     
     ##### List of pipeline input properties 
     > | S.No | Column name         | Property label                      | Property key    | Property value | Condition |
     > |------|---------------------|-------------------------------------|-----------------|----------------|-----------|
     > | 1    | Form Factor         | Form Factor                         | form_factor     | -              | -         |
     > | 2    | CLD Barcode         | CLD Barcode                         | cld_barcode     | -              | -         |
     > | 3    | Product Name        | Product Name                        | product_name    | -              | -         |
     > | 4    | Variant Barcode     | Barcode                             | variant_barcode | -              | -         |
     > | 5    | Material Code-Front | Front                               | material_code   | -              | -         |
     > | 6    | Material Code-Back  | Back                                | material_code   | -              | -         |
     > | 7    | Price               | Price                               | coding          | -              | -         |
     > | 8    | USP                 | USP                                 | coding          | -              | -         |
     > | 9    | Manufacturing Date  | Manufacturing Date                  | coding          | -              | -         |
     > | 10   | Expiry Date         | Expiry Date                         | coding          | -              | -         |
     > | 11   | Factory Code        | Factory Code                        | coding          | -              | -         |
     > | 12   | Target Weight (g)   | Weight                              | target_weight   | -              | -         |
     > | 13   | Tare Weight (g)     | Tare Weight                         | tare_weight     | -              | -         |
     > | 14   | -                   | Color: Matches with the standard?   | others          | -              | -         |
     > | 15   | -                   | Perfume: Matches with the standard? | others          | -              | -         |
     > | 16   | -                   | Min                                 | perforation     | NULL           | sachet    |
     > | 17   | -                   | Max                                 | perforation     | NULL           | sachet    |
     > | 18   | -                   | Avg                                 | perforation     | NULL           | sachet    |
     > | 19   | -                   | Raw                                 | perforation     | NULL           | sachet    |
     > | 20   | -                   | Front Face                          | pqs_carton      | 1              | norden    |
     > | 21   | -                   | Back Face                           | pqs_carton      | 1              | norden    |
     > | 22   | -                   | Left Face                           | pqs_carton      | 1              | norden    |
     > | 23   | -                   | Right Face                          | pqs_carton      | 1              | norden    |
     > | 24   | -                   | Top Face                            | pqs_carton      | 1              | norden    |
     > | 25   | -                   | Bottom Face                         | pqs_carton      | 1              | norden    |
     > | 26   | -                   | Damage                              | pqs_carton      | ''             | norden    |
     > | 27   | -                   | Flap Open                           | pqs_carton      | ''             | norden    |
     > | 28   | -                   | Dirt/Grease                         | pqs_carton      | ''             | norden    |
     > | 29   | -                   | Front Face                          | pqs_tube        | 1              | norden    |
     > | 30   | -                   | Back Face                           | pqs_tube        | 1              | norden    |
     > | 31   | -                   | Left Face                           | pqs_tube        | 1              | norden    |
     > | 32   | -                   | Right Face                          | pqs_tube        | 1              | norden    |
     > | 33   | -                   | Top Face                            | pqs_tube        | 1              | norden    |
     > | 34   | -                   | Bottom Face                         | pqs_tube        | 1              | norden    |
     > | 35   | -                   | Damage                              | pqs_tube        | ''             | norden    |
     > | 36   | -                   | Flap Open                           | pqs_tube        | ''             | norden    |
     > | 37   | -                   | Dirt/Grease                         | pqs_tube        | ''             | norden    |

     ##### Payload
     > | name   | type     | data type      | description              |
     > |--------|----------|----------------|--------------------------|
     > | `file` | required | form/multipart | CSV file containing data |
        
     ##### Responses
     > | http code | content-type                     | response |
     > |-----------|----------------------------------|----------|
     > | `201`     | `application/json;charset=UTF-8` | {}       |
     > | `400`     | `application/json;charset=UTF-8` | {}       |
     > | `500`     | `application/json;charset=UTF-8` | {}       |
        
     ##### Example cURL
        
     > ```bash
     >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/pipeline-input/all
     > ```
        
     </details>
        

* #### Listing existing pipeline input
    <details>
      <summary><code>GET</code> <code><b>/pipeline-input/{id}</b></code> <code>(gets a pipeline input by id)</code></summary>
        
     ##### Parameters
    > | name |  type     | data type    | description       |
    > |------|-----------|--------------|-------------------|
    > | `id` |  required | int          | Pipeline Input ID |
        
     ##### Responses
    > | http code | content-type                     | response |
    > |-----------|----------------------------------|----------|
    > | `200`     | `application/json;charset=UTF-8` | payload  |
        
     ##### Example cURL
        
    > ```bash
    >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/pipeline-input/1
    > ```
        
     </details>
        
     <details>
      <summary><code>GET</code> <code><b>/pipeline-input/all</b></code> <code>(gets all pipeline inputs)</code></summary>
        
     ##### Parameters
    > None
        
     ##### Responses
    > | http code | content-type                     | response |
    > |-----------|----------------------------------|----------|
    > | `200`     | `application/json;charset=UTF-8` | payload  |
        
     ##### Example cURL
        
    > ```bash
    >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/pipeline-input/all
    > ```
        
     </details>


### 5) Pipeline Session
    
   * #### Creating new pipeline session
        <details>
         <summary><code>POST</code> <code><b>/pipeline-session/new?user={}</b></code> <code>(creates new pipeline session)</code></summary>
     
        ##### Flow
        A *user* has to be *authorized* to call this endpoint. `created_by` carries the `id` of the *user* which should be directly
        fetched using the *authorization token* if the *created_by* parameter is *NULL*, else use the provided *created_by* directly.
     
        ##### Payload
        > | name                | type     | data type | description       |
        > |---------------------|----------|-----------|-------------------|
        > | `application_id`    | required | int       | Application ID    |
        > | `pipeline_input_id` | required | int       | Pipeline Input ID |
        > | `name`              | optional | string    | Any specific name |
        > | `created_by`        | optional | int       | ID of the user    |
        
        ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `201`     | `application/json;charset=UTF-8` | {}       |
        > | `400`     | `application/json;charset=UTF-8` | {}       |
        > | `500`     | `application/json;charset=UTF-8` | {}       |
   
        ##### Example cURL
        
        > ```bash
        >  curl -X POST -H "Content-Type: application/json" http://localhost:8000/api/v1/machine/new
        > ```
        
        </details>
     
   * #### Listing existing pipeline sessions
       <details>
      <summary><code>GET</code> <code><b>/pipeline-session/{id}?overview={overview}</b></code> <code>(gets a pipeline session by id)</code></summary>
        
     ##### Parameters
        > | name       | type     | data type | description                                                                                                                                                   |
        > |------------|----------|-----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
        > | `id`       | required | int       | The pipeline session ID                                                                                                                                       |
        > | `overview` | required | int       | If `0`, all the related `pipeline_session_output` and `pipeline_session_output_unit`<br/>should be fetched, else, return just<br/>the `pipeline_session` data |
        
     ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `200`     | `application/json;charset=UTF-8` | payload  |
        
     ##### Example cURL
        
        > ```bash
        >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/pipeline-session/1
        > ```
        
     </details>
        
     <details>
      <summary><code>GET</code> <code><b>/pipeline-session/all</b></code> <code>(gets all pipeline sessions)</code></summary>
        
     ##### Parameters
        > None
        
     ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `200`     | `application/json;charset=UTF-8` | payload  |
        
     ##### Example cURL
        
        > ```bash
        >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/pipeline-session/all
        > ```
        
     </details>

### 6) Pipeline Session Output
    
   * #### Creating new pipeline session output
        <details>
         <summary><code>POST</code> <code><b>/pipeline-session-output/new?manual={manual}&property-key={}</b></code> <code>(creates new pipeline session output)</code></summary>
     
        ##### Flow
        There are two ways that a *pipeline session output* can be created, manual or automatic. In manual mode, the session is typically
        controlled by a user where they choose when to run the pipeline. In this case, we need to prefill the `pipeline_session_output_unit` with
        the defined properties of *pipeline input* found in `general_property`. This is essentially to show the users of all the *analysis* they 
        have to perform. Prefilled entries will start out with `NULL` *property_value* which then will be added when the user runs the pipeline.
        In automatic mode, the pipeline will keep running where the *user* is not involved at all, therefore *pipeline_session_output_unit* will
        be created on demand.
        
        There is an option to create selective *pipeline session output units* based on the `property_key` parameter. By default, use all 
        properties found in *general property*. 
        
        **Example**: `property_key=coding,perforation`, in this case, create *pipeline session output unit* 
        entries only for *coding* and *peforation* entries found in *general property*.
        > Note: *property_key* is applicable only in *manual* mode.
     
        ##### Payload
        > | name                  | type     | data type | description                                              |
        > |-----------------------|----------|-----------|----------------------------------------------------------|
        > | `pipeline_session_id` | required | int       | Pipeline session ID                                      |
        > | `manual`              | optional | int       | Whether the session is created manually or automatically |
        > | `property-key`        | optional | string    | Comma separated property keys                            |
        
        ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `201`     | `application/json;charset=UTF-8` | {}       |
        > | `400`     | `application/json;charset=UTF-8` | {}       |
        > | `500`     | `application/json;charset=UTF-8` | {}       |
   
        ##### Example cURL
        
        > ```bash
        >  curl -X POST -H "Content-Type: application/json" http://localhost:8000/api/v1/machine/new
        > ```
        
   </details>
     
   * #### Listing existing pipeline sessions
       <details>
      <summary><code>GET</code> <code><b>/pipeline-session-output/{id}?overview={overview}</b></code> <code>(gets a pipeline session output by id)</code></summary>
        
     ##### Parameters
        > | name       | type     | data type | description                                                                                                                                        |
        > |------------|----------|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------|
        > | `id`       | required | int       | The pipeline session output ID                                                                                                                     |
        > | `overview` | optional | int       | `Default: 1`. <br/>If `0`, all the related `pipeline_session_output_unit`<br/>should be fetched, else, return just<br/>the `pipeline_session` data |
        
     ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `200`     | `application/json;charset=UTF-8` | payload  |
        
     ##### Example cURL
        
        > ```bash
        >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/pipeline-session-output/1
        > ```
        
     </details>
        
     <details>
      <summary><code>GET</code> <code><b>/pipeline-session-output/all?overview={overview}</b></code> <code>(gets all pipeline session outputs)</code></summary>
        
     ##### Parameters
        > | name       | type     | data type | description                                                                                                                                        |
        > |------------|----------|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------|
        > | `overview` | optional | int       | `Default: 1`. <br/>If `0`, all the related `pipeline_session_output_unit`<br/>should be fetched, else, return just<br/>the `pipeline_session` data |
        
     ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `200`     | `application/json;charset=UTF-8` | payload  |
        
     ##### Example cURL
        
        > ```bash
        >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/pipeline-session/all
        > ```
        
     </details>

### 7) Pipeline Session Output Unit
    
   * #### Creating new pipeline session output unit
        <details>
         <summary><code>POST</code> <code><b>/pipeline-session-output-unit/new</b></code> <code>(creates new pipeline session output unit)</code></summary>
     
        ##### Payload
        > | name                         | type     | data type | description                                              |
        > |------------------------------|----------|-----------|----------------------------------------------------------|
        > | `pipeline_session_output_id` | required | int       | Pipeline session output ID                               |
        > | `property_reference_id`      | required | int       | ID of the general property reference                     |
        > | `name`                       | optional | string    | Any descriptive name                                     |
        > | `output_key`                 | required | string    | Output value's property name (like general property key) |
        > | `output_value`               | required | string    | Output value                                             |
        > | `status`                     | optional | string    | Status of the unit. `Default: success`                   |
        
        ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `201`     | `application/json;charset=UTF-8` | {}       |
        > | `400`     | `application/json;charset=UTF-8` | {}       |
        > | `500`     | `application/json;charset=UTF-8` | {}       |
   
        ##### Example cURL
        
        > ```bash
        >  curl -X POST -H "Content-Type: application/json" http://localhost:8000/api/v1/machine/new
        > ```
        
   </details>
     
   * #### Listing existing pipeline session units
       <details>
      <summary><code>GET</code> <code><b>/pipeline-session-output-unit/{id}</b></code> <code>(gets a pipeline session output unit by id)</code></summary>
        
     ##### Parameters
        > | name       | type     | data type | description                                                                                                                                        |
        > |------------|----------|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------|
        > | `id`       | required | int       | The pipeline session output ID                                                                                                                     |
        
     ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `200`     | `application/json;charset=UTF-8` | payload  |
        
     ##### Example cURL
        
        > ```bash
        >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/pipeline-session-output-unit/1
        > ```
        
     </details>
        
     <details>
      <summary><code>GET</code> <code><b>/pipeline-session-output-unit/all?pipeline-session-output-id={}</b></code> <code>(gets all pipeline session output units for a pipeline session output)</code></summary>
        
     ##### Parameters
        > | name                         | type     | data type | description                |
        > |------------------------------|----------|-----------|----------------------------|
        > | `pipeline-session-output-id` | required | int       | Pipeline session output ID |
        
     ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `200`     | `application/json;charset=UTF-8` | payload  |
        
     ##### Example cURL
        
        > ```bash
        >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/pipeline-session-output-unit/all?pipeline-session-output-id=1
        > ```
        
     </details>
     
   * #### Updating existing pipeline session output unit
      <details>
       <summary><code>PATCH</code> <code><b>/pipeline-session-output-unit/{id}</b></code> <code>(updates existing pipeline session output unit)</code></summary>
      
      ##### Parameter
        > | name | type     | data type | description                     |
        > |------|----------|-----------|---------------------------------|
        > | `id` | required | int       | Pipeline session output unit ID |
     
      ##### Payload
        > | name                    | type     | data type | description                                              |
        > |-------------------------|----------|-----------|----------------------------------------------------------|
        > | `property_reference_id` | optional | int       | ID of the general property reference                     |
        > | `name`                  | optional | string    | Any descriptive name                                     |
        > | `output_key`            | optional | string    | Output value's property name (like general property key) |
        > | `output_value`          | optional | string    | Output value                                             |
        > | `status`                | optional | string    | Status of the unit. `Default: success`                   |
        
      ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `204`     | `application/json;charset=UTF-8` | {}       |
        > | `400`     | `application/json;charset=UTF-8` | {}       |
        > | `500`     | `application/json;charset=UTF-8` | {}       |
   
      ##### Example cURL
        
        > ```bash
        >  curl -X PATCH -H "Content-Type: application/json" http://localhost:8000/api/v1/pipeline-session-output-unit/1
        > ```
        
      </details>
      <details>
       <summary><code>PATCH</code> <code><b>/pipeline-session-output-unit/all?pipeline-session-output-id={}&output-key={}</b></code> 
        <code>(updates all existing pipeline session output units of a pipeline session output)</code></summary>
     
      ##### Context
      This endpoint is essentially useful in cases of manual pipeline sessions where we have to reset the old *output values* and retry again. In that case
      we need to set *status* to *ready/idle* and set *output_value* to *NULL*.
      
      Parameters *pipeline-session-output-id* & *output-key* work in a heirarchical way.
      > Case 1: Assume *pipeline-session-output-id=1*, here, all the 
      *pipeline session output units* having *pipeline_session_output_id=1* will be updated with the given payload.
      
      > Case 2: Assume *pipeline-session-output-id=1 & output-key=coding*, here, all the 
      *pipeline session output units* having *pipeline_session_output_id=1* and *output_key=coding* will be updated with the given payload.
      
      ##### Parameter
        > | name                         | type     | data type | description                                              |
        > |------------------------------|----------|-----------|----------------------------------------------------------|
        > | `pipeline-session-output-id` | optional | int       | Pipeline session output ID                               |
        > | `output-key`                 | optional | int       | Output value's property name (like general property key) |
      
      ##### Payload
        > | name                         | type     | data type | description                                              |
        > |------------------------------|----------|-----------|----------------------------------------------------------|
        > | `pipeline-session-output-id` | optional | int       | Pipeline session output ID                               |
        > | `property_reference_id`      | optional | int       | ID of the general property reference                     |
        > | `name`                       | optional | string    | Any descriptive name                                     |
        > | `output_key`                 | optional | string    | Output value's property name (like general property key) |
        > | `output_value`               | optional | string    | Output value                                             |
        > | `status`                     | optional | string    | Status of the unit. `Default: success`                   |
        
      ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `204`     | `application/json;charset=UTF-8` | {}       |
        > | `400`     | `application/json;charset=UTF-8` | {}       |
        > | `500`     | `application/json;charset=UTF-8` | {}       |
   
      ##### Example cURL
        
        > ```bash
        >  curl -X PATCH -H "Content-Type: application/json" http://localhost:8000/api/v1/pipeline-session-output-unit/all?pipeline-session-output-id=1
        > ```
        
      </details>
   
### 6) Insight
    
   * #### Getting pipeline session insight
        <details>
         <summary><code>GET</code> <code><b>/insight/pipeline-session-by-attribute?attr={}&st={}&et={}&shift={}&pid={}&vid={}&created-by={}&page={}</b></code> <code>(gets pipeline session insight attribute wise)</code></summary>
     
        ##### Parameters
        > | name         | type     | data type | description                                                                                  |
        > |--------------|----------|-----------|----------------------------------------------------------------------------------------------|
        > | `attr`       | required | string    | Attribute linked to pipeline session (created_by, pipeline_input_id, product_id, created_at) |
        > | `st`         | optional | int       | Start time in unix milliseconds                                                              |
        > | `et`         | optional | int       | End time in unix milliseconds                                                                |
        > | `shift`      | optional | int       | Work shift (1 -> 7 to 15, 2 -> 15 to 23, 3 -> 23 - 7)                                        |
        > | `pid`        | optional | int       | Product ID (pipeline sessions associated with this product)                                  |
        > | `vid`        | optional | int       | Variant ID (pipeline sessions associated with this variant)                                  |
        > | `page`       | optional | int       | Page no (pagination)                                                                         |
        > | `created-by` | optional | int       | User ID                                                                                      |
        
        ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `200`     | `application/json;charset=UTF-8` | {}       |
        > | `400`     | `application/json;charset=UTF-8` | {}       |
        > | `500`     | `application/json;charset=UTF-8` | {}       |
   
        ##### Example cURL
        
        > ```bash
        >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/insight/pipeline-session-by-attribute?attr=created_at
        > ```
        
        #### Example Response
        
        > | Attribute         | Label   | Value        |
        > |-------------------|---------|--------------|
        > | created_at        | Date    | dd/mm/yy     |
        > | pipeline_input_id | Variant | variant name |
        > | product_id        | Product | product name |
        > | created_by        | User    | username     |
        
        ```json
        {
          "pagination": {
            "page_no": 1,
            "page_size": 100,
            "total_available": 3
          },
          "overview": {
            "total": 23,
            "failed": 5,
            "passed": 18,
            "pass_percent": 78.2,
            "fail_percent": 21.8
          },
          "expanded": [
            {
              "attribute": {
                "label": "date",
                "value": "15/01/25"
              },
              "total": 3,
              "failed": 0,
              "passed": 3,
              "pass_percent": 100,
              "fail_percent": 0
            },
            {
              "attribute": {
                "label": "date",
                "value": "16/01/25"
              },
              "total": 10,
              "failed": 2,
              "passed": 8,
              "pass_percent": 80,
              "fail_percent": 20
            },
            {
              "attribute": {
                "label": "date",
                "value": "17/01/25"
              },
              "total": 10,
              "failed": 1,
              "passed": 9,
              "pass_percent": 90,
              "fail_percent": 10
            }
          ]  
        }
        ```
        
   </details>

   * #### Getting pipeline session verdict insight
        <details>
         <summary><code>GET</code> <code><b>/insight/pipeline-session-verdict?st={}&et={}&shift={}&pid={}&vid={}&created-by={}&page={}</b></code> <code>(gets pipeline session verdict insight day wise)</code></summary>
     
        ##### Parameters
        > | name         | type     | data type | description                                                 |
        > |--------------|----------|-----------|-------------------------------------------------------------|
        > | `st`         | optional | int       | Start time in unix milliseconds                             |
        > | `et`         | optional | int       | End time in unix milliseconds                               |
        > | `shift`      | optional | int       | Work shift (1 -> 7 to 15, 2 -> 15 to 23, 3 -> 23 - 7)       |
        > | `pid`        | optional | int       | Product ID (pipeline sessions associated with this product) |
        > | `vid`        | optional | int       | Variant ID (pipeline sessions associated with this variant) |
        > | `page`       | optional | int       | Page no (pagination)                                        |
        > | `created-by` | optional | int       | User ID                                                     |
        
        ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `200`     | `application/json;charset=UTF-8` | {}       |
        > | `400`     | `application/json;charset=UTF-8` | {}       |
        > | `500`     | `application/json;charset=UTF-8` | {}       |
   
        ##### Example cURL
        
        > ```bash
        >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/insight/pipeline-session-verdict
        > ```
        
        #### Example Response
        The verdict should resolve from bottom up, *pipeline session output unit > pipeline session output > pipeline session*.
        A *pipeline session output* should hold a combined verdict of *1* if all of its *pipeline input output units* hold verdict 
        of *1*. Same logic goes for *pipeline session verdict*. 
        
        ```json
        {
          "pagination": {
            "page_no": 1,
            "page_size": 50,
            "total_available": 3
          },
          "expanded": [
            {
              "id": 1,
              "pipeline_id": {
                "id": 1,
                "name": "QC Pipeline",
                "is_running": 1,
                "application_id": 1,
                "created_at": 162348732849
              },
              "pipeline_input_id": {
                "id": 1,
                "name": "Variant 1",
                "created_at": 162348732849
              },
              "name": "dummy name",
              "created_by": {
                "id": 1,
                "username": "username",
                "email_address": "email@email.com",
                "first_name": "name1",
                "last_name": "name2"
              },
              "created_at": 192437328730,
              "ended_at": 192437328830,
              "verdict": 1,
              "pipeline_output": [
                {
                  "id": 1,
                  "name": "Output 1",
                  "pipeline_session_id": 1,
                  "created_at": 162348733849,
                  "ended_at": 162348732849,
                  "verdict": 1,
                  "pipeline_output_unit": [
                    {
                      "id": 1,
                      "pipeline_session_output_id": 1,
                      "property_reference_id": {
                          "id": 1,
                          "referrer_id": 1,
                          "property_type": "pipeline_input",
                          "property_label": "Price",
                          "property_key": "coding",
                          "property_value": "220/-",
                          "tags": "ui,input",
                          "created_at": 162348732849
                        },
                      "name": "Price",
                      "output_key": "coding",
                      "output_value": "220/-",
                      "status": "success",
                      "created_at": 162348732849,
                      "verdict": 1
                    },
                    {
                      "id": 2,
                      "pipeline_session_output_id": 1,
                      "property_reference_id": {
                          "id": 2,
                          "referrer_id": 1,
                          "property_type": "pipeline_input",
                          "property_label": "USP",
                          "property_key": "coding",
                          "property_value": "2.23",
                          "tags": "ui,input",
                          "created_at": 162348732849
                        },
                      "name": "USP",
                      "output_key": "coding",
                      "output_value": "2.23",
                      "status": "success",
                      "created_at": 162348732849,
                      "verdict": 1
                    }
                  ]    
                }
              ]    
            }
          ]  
        }
        ```

   </details>

   * #### Getting pipeline session output unit insight
        <details>
         <summary><code>GET</code> <code><b>/insight/pipeline-session-output-unit-by-attribute?attr={}&property-label={}&st={}&et={}&shift={}&pid={}&vid={}&created-by={}&page={}</b></code> <code>(gets pipeline session output unit insight attribute wise)</code></summary>
     
        > Note: Currently supports only *number* valued units
     
        ##### Parameters
        > | name             | type     | data type | description                                                                                  |
        > |------------------|----------|-----------|----------------------------------------------------------------------------------------------|
        > | `attr`           | required | string    | Attribute linked to pipeline session (created_by, pipeline_input_id, product_id, created_at) |
        > | `property-label` | required | string    | Property label linked to pipeline session output unit                                        |
        > | `st`             | optional | int       | Start time in unix milliseconds                                                              |
        > | `et`             | optional | int       | End time in unix milliseconds                                                                |
        > | `shift`          | optional | int       | Work shift (1 -> 7 to 15, 2 -> 15 to 23, 3 -> 23 - 7)                                        |
        > | `pid`            | optional | int       | Product ID (pipeline sessions associated with this product)                                  |
        > | `vid`            | optional | int       | Variant ID (pipeline sessions associated with this variant)                                  |
        > | `page`           | optional | int       | Page no (pagination)                                                                         |
        > | `created-by`     | optional | int       | User ID                                                                                      |
        
        ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `200`     | `application/json;charset=UTF-8` | {}       |
        > | `400`     | `application/json;charset=UTF-8` | {}       |
        > | `500`     | `application/json;charset=UTF-8` | {}       |
   
        ##### Example cURL
        
        > ```bash
        >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/insight/pipeline-session-output-unit?property-label=Weight&attr=product_id
        > ```
        
        #### Example Response
        
        ```json
        {
          "pagination": {
            "page_no": 1,
            "page_size": 100,
            "total_available": 3
          },
          "overview": {
            "total": 23,
            "failed": 5,
            "passed": 18,
            "pass_percent": 78.2,
            "fail_percent": 21.8
          },
          "expanded": [
            {
              "attribute": {
                "label": "Product",
                "value": "Dove"
              },
              "min": 0,
              "max": 5,
              "avg": 2.5
            },
            {
              "attribute": {
                "label": "Product",
                "value": "SUNSILK"
              },
              "min": 0,
              "max": 5,
              "avg": 2.5
            },
            {
              "attribute": {
                "label": "Product",
                "value": "CLINIC PLUS"
              },
              "min": 0,
              "max": 5,
              "avg": 2.5
            }
          ]  
        }
        ```
        
   </details>

   * #### Getting PQS insight
        <details>
         <summary><code>GET</code> <code><b>/insight/pqs?st={}&et={}&shift={}&pid={}&vid={}&created-by={}&page={}</b></code> <code>(gets pqs analysis insight)</code></summary>
          
        ##### Parameters
        > | name             | type     | data type | description                                                                                  |
        > |------------------|----------|-----------|----------------------------------------------------------------------------------------------|
        > | `st`             | optional | int       | Start time in unix milliseconds                                                              |
        > | `et`             | optional | int       | End time in unix milliseconds                                                                |
        > | `shift`          | optional | int       | Work shift (1 -> 7 to 15, 2 -> 15 to 23, 3 -> 23 - 7)                                        |
        > | `pid`            | optional | int       | Product ID (pipeline sessions associated with this product)                                  |
        > | `vid`            | optional | int       | Variant ID (pipeline sessions associated with this variant)                                  |
        > | `page`           | optional | int       | Page no (pagination)                                                                         |
        > | `created-by`     | optional | int       | User ID                                                                                      |
        
        ##### Responses
        > | http code | content-type                     | response |
        > |-----------|----------------------------------|----------|
        > | `200`     | `application/json;charset=UTF-8` | {}       |
        > | `400`     | `application/json;charset=UTF-8` | {}       |
        > | `500`     | `application/json;charset=UTF-8` | {}       |
   
        ##### Example cURL
        
        > ```bash
        >  curl -X GET -H "Content-Type: application/json" http://localhost:8000/api/v1/insight/pqs
        > ```
        
        #### Example Response
        
        ```json
        {
          "pagination": {
            "page_no": 1,
            "page_size": 100,
            "total_available": 3
          },
          "overview": {
            "total": 23,
            "failed": 5,
            "passed": 18,
            "pass_percent": 78.2,
            "fail_percent": 21.8
          },
          "expanded": [
            {
              "attribute": {
                "label": "Product",
                "value": "Dove"
              },
              "min": 0,
              "max": 5,
              "avg": 2.5
            },
            {
              "attribute": {
                "label": "Product",
                "value": "SUNSILK"
              },
              "min": 0,
              "max": 5,
              "avg": 2.5
            },
            {
              "attribute": {
                "label": "Product",
                "value": "CLINIC PLUS"
              },
              "min": 0,
              "max": 5,
              "avg": 2.5
            }
          ]  
        }
        ```
  </details>