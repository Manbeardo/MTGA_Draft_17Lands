from pydantic import BaseModel


class Features(BaseModel):
    """This class represents a collection of features that can be enabled or disabled within the overlay"""
    override_scale_factor: float = 0.0
    hotkey_enabled: bool = True
    images_enabled: bool = True