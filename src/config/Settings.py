from src import constants


from pydantic import BaseModel, validator


class Settings(BaseModel):
    """This class holds UI settings"""
    table_width: int = 270
    column_2: str = constants.COLUMNS_OPTIONS_EXTRA_DICT[constants.COLUMN_2_DEFAULT]
    column_3: str = constants.COLUMNS_OPTIONS_EXTRA_DICT[constants.COLUMN_3_DEFAULT]
    column_4: str = constants.COLUMNS_OPTIONS_EXTRA_DICT[constants.COLUMN_4_DEFAULT]
    column_5: str = constants.COLUMNS_OPTIONS_EXTRA_DICT[constants.COLUMN_5_DEFAULT]
    column_6: str = constants.COLUMNS_OPTIONS_EXTRA_DICT[constants.COLUMN_6_DEFAULT]
    column_7: str = constants.COLUMNS_OPTIONS_EXTRA_DICT[constants.COLUMN_7_DEFAULT]
    deck_filter: str = constants.DECK_FILTER_DEFAULT
    filter_format: str = constants.DECK_FILTER_FORMAT_COLORS
    result_format: str = constants.RESULT_FORMAT_WIN_RATE
    ui_size: str = constants.UI_SIZE_DEFAULT
    card_colors_enabled: bool = False
    missing_enabled: bool = True
    stats_enabled: bool = False
    auto_highest_enabled: bool = True
    curve_bonus_enabled: bool = False
    color_bonus_enabled: bool = False
    bayesian_average_enabled: bool = False
    draft_log_enabled: bool = True
    color_identity_enabled: bool = False
    current_draft_enabled: bool = True
    data_source_enabled: bool = True
    deck_filter_enabled: bool = True
    refresh_button_enabled: bool = True
    taken_alsa_enabled: bool = False
    taken_ata_enabled: bool = False
    taken_gpwr_enabled: bool = False
    taken_ohwr_enabled: bool = False
    taken_gdwr_enabled: bool = False
    taken_gndwr_enabled: bool = False
    taken_iwd_enabled: bool = False
    arena_log_location: str = ""

    @validator('deck_filter')
    def validate_deck_filter(cls, value, field):
        allowed_values = constants.DECK_FILTERS  # List of options
        field_name = field.name
        if value not in allowed_values:
            return cls.__fields__[field_name].default
        return value

    @validator('filter_format')
    def validate_filter_format(cls, value, field):
        allowed_values = constants.DECK_FILTER_FORMAT_LIST  # List of options
        field_name = field.name
        if value not in allowed_values:
            return cls.__fields__[field_name].default
        return value

    @validator('result_format')
    def validate_result_format(cls, value, field):
        allowed_values = constants.RESULT_FORMAT_LIST  # List of options
        field_name = field.name
        if value not in allowed_values:
            return cls.__fields__[field_name].default
        return value

    @validator('ui_size')
    def validate_ui_size(cls, value, field):
        allowed_values = constants.UI_SIZE_DICT  # List of options
        field_name = field.name
        if value not in allowed_values:
            return cls.__fields__[field_name].default
        return value