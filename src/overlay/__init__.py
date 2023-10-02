"""This module contains the functions and classes that are used for building and handling the application UI"""
import tkinter
import math
import argparse
import webbrowser
from src.logger import create_logger
from src import card_logic as CL
from src import constants

def check_version(update, version):
    """Compare the application version and the latest version in the repository"""
    return_value = False
    file_version, file_location = update.retrieve_file_version()
    if file_version:
        file_version = int(file_version)
        client_version = round(float(version) * 100)
        if file_version > client_version:
            return_value = True

        file_version = round(float(file_version) / 100.0, 2)
    return return_value, file_version, file_location


def fixed_map(style, option):
    ''' Returns the style map for 'option' with any styles starting with
     ("!disabled", "!selected", ...) filtered out
     style.map() returns an empty list for missing options, so this should
     be future-safe'''
    return [elm for elm in style.map("Treeview", query_opt=option)
            if elm[:2] != ("!disabled", "!selected")]


def control_table_column(table, column_fields, table_width=None):
    """Hide disabled table columns"""
    visible_columns = {}
    last_field_index = 0
    for count, (key, value) in enumerate(column_fields.items()):
        if value != constants.DATA_FIELD_DISABLED:
            table.heading(key, text=value.upper())
            # visible_columns.append(key)
            visible_columns[key] = count
            last_field_index = count

    table["displaycolumns"] = list(visible_columns.keys())

    # Resize columns if there are fewer than 4
    if table_width:
        total_visible_columns = len(visible_columns)
        width = table_width
        offset = 0
        if total_visible_columns <= 4:
            proportions = constants.TABLE_PROPORTIONS[total_visible_columns - 1]
            for column in table["displaycolumns"]:
                column_width = min(int(math.ceil(
                    proportions[offset] * table_width)), width)
                width -= column_width
                offset += 1
                table.column(column, width=column_width)

            table["show"] = "headings"  # use after setting columns

    return last_field_index, visible_columns


logger = create_logger()


def copy_suggested(deck_colors, deck, color_options):
    """Copy the deck and sideboard list from the Suggest Deck window"""
    colors = color_options[deck_colors.get()]
    deck_string = ""
    try:
        deck_string = CL.copy_deck(
            deck[colors]["deck_cards"], deck[colors]["sideboard_cards"])
        copy_clipboard(deck_string)
    except Exception as error:
        logger.error(error)
    return


def copy_taken(taken_cards):
    """Copy the card list from the Taken Cards window"""
    deck_string = ""
    try:
        stacked_cards = CL.stack_cards(taken_cards)
        deck_string = CL.copy_deck(
            stacked_cards, None)
        copy_clipboard(deck_string)

    except Exception as error:
        logger.error(error)
    return


def copy_clipboard(copy):
    """Send the copied data to the clipboard"""
    try:
        # Attempt to copy to clipboard
        clip = tkinter.Tk()
        clip.withdraw()
        clip.clipboard_clear()
        clip.clipboard_append(copy)
        clip.update()
        clip.destroy()
    except Exception as error:
        logger.error(error)
    return


def identify_table_row_tag(colors_enabled, colors, index):
    """Return the row color (black/white or card color) depending on the application settings"""
    tag = ""

    if colors_enabled:
        tag = CL.row_color_tag(colors)
    else:
        tag = constants.BW_ROW_COLOR_ODD_TAG if index % 2 else constants.BW_ROW_COLOR_EVEN_TAG

    return tag


def identify_safe_coordinates(root, window_width, window_height, offset_x, offset_y):
    '''Return x,y coordinates that fall within the bounds of the screen'''
    location_x = 0
    location_y = 0

    try:
        pointer_x = root.winfo_pointerx()
        pointer_y = root.winfo_pointery()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        if pointer_x + offset_x + window_width > screen_width:
            location_x = max(pointer_x - offset_x - window_width, 0)
        else:
            location_x = pointer_x + offset_x

        if pointer_y + offset_y + window_height > screen_height:
            location_y = max(pointer_y - offset_y - window_height, 0)
        else:
            location_y = pointer_y + offset_y

    except Exception as error:
        logger.error(error)

    return location_x, location_y


def toggle_widget(input_widget, enable):
    '''Hide/Display a UI widget'''
    try:
        if enable:
            input_widget.grid()
        else:
            input_widget.grid_remove()
    except Exception as error:
        logger.error(error)


def identify_card_row_tag(configuration, card_data, count):
    '''Wrapper function for setting the row color for a card'''
    if configuration.color_identity_enabled or constants.CARD_TYPE_LAND in card_data[constants.DATA_FIELD_TYPES]:
        colors = card_data[constants.DATA_FIELD_COLORS]
    else:
        colors = card_data[constants.DATA_FIELD_MANA_COST]

    row_tag = identify_table_row_tag(
        configuration.card_colors_enabled, colors, count)

    return row_tag


def disable_resizing(event, table):
    '''Disable the column resizing for a treeview table'''
    if table.identify_region(event.x, event.y) == "separator":
        return "break"


def url_callback(event):
    webbrowser.open_new(event.widget.cget("text"))


APPLICATION_VERSION = 3.10
HOTKEY_CTRL_G = '\x07'

