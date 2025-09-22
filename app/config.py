from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Manages application-wide settings and secrets.

    This class uses pydantic-settings to automatically read environment variables
    from a .env file, providing type validation and a centralized configuration point.
    """

    # The variable name here MUST match the one in your .env file (case-sensitive).
    GEMINI_API_KEY: str

    
    firebase_project_id: str
    firebase_client_email: str
    firebase_private_key: str
    firebase_api_key: str
    firebase_auth_domain: str
    firebase_messaging_sender_id: str
    firebase_app_id: str

    # This model_config dictionary tells Pydantic how to behave.
    # `env_file=".env"` explicitly instructs it to load settings from a file named '.env'.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8'  # Good practice to specify encoding
    )


# Create a single, global instance of the Settings class.
# This instance will be imported by other modules to access the settings.
# The validation error you saw happens on this line if the .env file is not found or is missing a key.
settings = Settings()
