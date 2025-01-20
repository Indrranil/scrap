# ROLE_PERMISSIONS = {
#     "app_admin": [
#         # Pipeline permissions
#         "create:pipeline", "read:pipeline", "update:pipeline", "delete:pipeline",
        
#         # Machine permissions
#         "create:machine", "read:machine", "update:machine", "delete:machine",
        
#         # Application permissions
#         "create:application", "read:application", "update:application", "delete:application",
        
#         # Application Container permissions
#         "create:application_container", "read:application_container", "delete:application_container",
        
#         # Application Session permissions
#         "create:application_session", "read:application_session", "update:application_session", "delete:application_session",
        
#         # Application Session Unit permissions
#         "create:application_session_unit", "read:application_session_unit", "update:application_session_unit", "delete:application_session_unit",
        
#         # Application Session Unit Output permissions
#         "create:application_session_unit_output", "read:application_session_unit_output", "update:application_session_unit_output", "delete:application_session_unit_output",
        
#         # Application Status Log permissions
#         "create:application_status_log", "read:application_status_log",
        
#         # Pipeline Input permissions
#         "create:pipeline_input", "read:pipeline_input", "update:pipeline_input", "delete:pipeline_input",
        
#         # Pipeline Input Referrer permissions
#         "create:pipeline_input_referrer", "read:pipeline_input_referrer", "update:pipeline_input_referrer", "delete:pipeline_input_referrer",
        
#         # General Property permissions
#         "create:general_property", "read:general_property", "update:general_property", "delete:general_property",
#     ],
    
#     "app_user": [
#         # Read permissions
#         "read:pipeline", "read:machine", "read:application",
        
#         # Pipeline Input permissions
#         "create:pipeline_input", "read:pipeline_input", "update:pipeline_input",
        
#         # Application Session permissions (for their own sessions)
#         "create:application_session", "read:application_session", "update:application_session",
        
#         # Application Session Unit permissions
#         "create:application_session_unit", "read:application_session_unit",
        
#         # Application Session Unit Output permissions
#         "read:application_session_unit_output",
        
#         # Application Status Log permissions
#         "read:application_status_log",
        
#         # Pipeline Input Referrer permissions
#         "read:pipeline_input_referrer"
#     ]
# }

ROLE_PERMISSIONS = {
    "app_admin": [
        "create_pipeline_session", "read_pipeline_session", "update_pipeline_session", "delete_pipeline_session"]
    ,
    "app_user": [
        "read_pipeline_session", "create_pipeline_session", "update_pipeline_session"]
}