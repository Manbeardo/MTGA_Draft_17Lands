from src import constants
from src import card_logic as CL
from src.overlay import logger
from src.overlay.TableInfo import TableInfo
from src.overlay import disable_resizing, identify_table_row_tag


import math
import tkinter
from tkinter.ttk import Treeview


class ScaledWindow:
    def __init__(self):
        self.scale_factor = 1
        self.fonts_dict = {}
        self.table_info = {}

    def _scale_value(self, value):
        scaled_value = int(value * self.scale_factor)

        return scaled_value

    def _create_header(self, table_label, frame, height, font, headers, total_width, include_header, fixed_width, table_style, stretch_enabled):
        """Configure the tkinter Treeview widget tables that are used to list draft data"""
        header_labels = tuple(headers.keys())
        show_header = "headings" if include_header else ""
        column_stretch = tkinter.YES if stretch_enabled else tkinter.NO
        list_box = Treeview(frame, columns=header_labels,
                            show=show_header, style=table_style, height=height)

        try:
            for key, value in constants.ROW_TAGS_BW_DICT.items():
                list_box.tag_configure(
                    key, font=(value[0], font, "bold"), background=value[1], foreground=value[2])

            for key, value in constants.ROW_TAGS_COLORS_DICT.items():
                list_box.tag_configure(
                    key, font=(value[0], font, "bold"), background=value[1], foreground=value[2])

            for column in header_labels:
                if fixed_width:
                    column_width = int(
                        math.ceil(headers[column]["width"] * total_width))
                    list_box.column(column,
                                    stretch=column_stretch,
                                    anchor=headers[column]["anchor"],
                                    width=column_width)
                else:
                    list_box.column(column, stretch=column_stretch,
                                    anchor=headers[column]["anchor"])
                list_box.heading(column, text=column, anchor=tkinter.CENTER,
                                 command=lambda _col=column: self._sort_table_column(table_label, list_box, _col, True))
            list_box["show"] = show_header  # use after setting columns
            if include_header:
                list_box.bind(
                    '<Button-1>', lambda event: disable_resizing(event, table=list_box))
            self.table_info[table_label] = TableInfo()
        except Exception as error:
            logger.error(error)
        return list_box

    def _sort_table_column(self, table_label, table, column, reverse):
        """Sort the table columns when clicked"""
        row_colors = False

        try:
            # Sort column that contains numeric values
            row_list = [(float(table.set(k, column)), k)
                        for k in table.get_children('')]
        except ValueError:
            # Sort column that contains string values
            row_list = [(table.set(k, column), k)
                        for k in table.get_children('')]

        row_list.sort(key=lambda x: CL.field_process_sort(
            x[0]), reverse=reverse)

        if row_list:
            tags = table.item(row_list[0][1])["tags"][0]
            row_colors = True if tags in constants.ROW_TAGS_COLORS_DICT else False

        for index, value in enumerate(row_list):
            table.move(value[1], "", index)

            # Reset the black/white shades for sorted rows
            if not row_colors:
                row_tag = identify_table_row_tag(False, "", index)
                table.item(value[1], tags=row_tag)

        if table_label in self.table_info:
            self.table_info[table_label].reverse = reverse
            self.table_info[table_label].column = column

        table.heading(column, command=lambda: self._sort_table_column(
            table_label, table, column, not reverse))