# Frontend Integration

1) CLD Barcode Analysis:

    Follow the following steps to take to do the `cld barcode analysis`:
    * Create a `pipeline session` with the following payload:
      ```json
      {
        "pipeline_id": 1,
        "pipeline_input_id": 1,
        "name": "CLD Analysis"
      }
      ```
    * Create a `pipeline session output` with the `manual` mode enabled & use the following payload:
      ```json
      {
        "pipeline_session_id": 1,
        "name": "CLD Barcode Analysis"
      }
      ```
      > `pipeline_session_id` is taken from the response of the new pipeline session 
      
    * Since the manual mode is enabled, a `pipeline session output unit` is created along with a `pipeline session output`.
      The unit will be in `idle` state. We have to update the state to `ready` for the pipeline to start.
    * Before updating the `pipeline session output unit`, we have to find the id of the unit. To do that,
      get the created `pipeline session` using its id with the `overview` disabled. The response contains the unit id.
    * Now update the unit's state to `ready` using its id.
    * Once the state is updated, monitor the state continuously to track the status of analysis. Once the unit reaches the 
      `success` state, the `output_value` contains the detected `cld barcode`.
    * Now, we have to find the respective `pipeline input id` (variant id). We can do that by using the get method in `general property` with the following flags,
      ```curl
      {{base_url}}/{{version}}/general-property?property_type=pipeline_input&property_key=cld_barcode&property_value=<cld_barcode>
      ```
    * The response contains a key `referrer_id`, which is the `pipeline input id`.
    * Using the `pipeline input id`, we can now create a `qc session` (pipeline session) in the same way we did for `cld barcode analysis`.
      
   