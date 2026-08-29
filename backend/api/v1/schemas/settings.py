from pydantic import BaseModel, Field


class SettingsPayload(BaseModel):
    """Admin-only configuration payload.

    M2 ships an explicit empty structure. Real configuration values arrive
    with the Digital Twin / Settings milestones.
    """

    settings: dict = Field(default_factory=dict)