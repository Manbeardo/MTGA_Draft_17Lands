from src import constants
from src.overlay import logger
from src.overlay import identify_safe_coordinates, identify_table_row_tag
from src.overlay.ScaledWindow import ScaledWindow


from PIL import Image, ImageFont, ImageTk


import io
import math
import sys
import tkinter
import urllib
from tkinter.ttk import Label, Style


class CardToolTip(ScaledWindow):
    '''Class that's used to create the card tooltip that appears when a table row is clicked'''

    def __init__(self, widget, event, card_name, color_dict, image, images_enabled, scale_factor, fonts_dict, tier_info):
        super().__init__()
        self.scale_factor = scale_factor
        self.fonts_dict = fonts_dict
        self.waittime = 1  # miliseconds
        self.widget = widget
        self.card_name = card_name
        self.color_dict = color_dict
        self.image = image
        self.images_enabled = images_enabled
        self.widget.bind("<Leave>", self.__leave)
        self.widget.bind("<ButtonPress-1>", self.__leave, add="+")

        self.id = None
        self.tw = None
        self.tier_info = tier_info
        self.event = event
        self.images = []
        self.__enter()

    def __enter(self, event=None):
        '''Initiate creation of the tooltip widget'''
        self.__schedule()

    def __leave(self, event=None):
        '''Remove tooltip when the user hovers over the tooltip or clicks elsewhere'''
        self.__unschedule()
        self.__hide_tooltip()

    def __schedule(self):
        '''Creates the tooltip window widget and stores the id'''
        self.__unschedule()
        self.id = self.widget.after(self.waittime, self.__display_tooltip)

    def __unschedule(self):
        '''Clear the stored widget data when the closing the tooltip'''
        widget_id = self.id
        self.id = None
        if widget_id:
            self.widget.after_cancel(widget_id)

    def __display_tooltip(self, event=None):
        '''Function that builds and populates the tooltip window '''
        try:
            row_height = self._scale_value(23)
            tt_width = 0
            tt_height = self._scale_value(450)
            # creates a toplevel window
            self.tw = tkinter.Toplevel(self.widget)
            # Leaves only the label and removes the app window
            self.tw.wm_overrideredirect(True)
            if sys.platform == constants.PLATFORM_ID_OSX:
                self.tw.wm_overrideredirect(False)

            tt_frame = tkinter.Frame(self.tw, borderwidth=5, relief="solid")

            tkinter.Grid.rowconfigure(tt_frame, 2, weight=1)

            card_label = Label(tt_frame,
                               text=self.card_name,
                               style="TooltipHeader.TLabel",
                               background="#3d3d3d",
                               foreground="#e6ecec",
                               relief="groove",
                               anchor="c",)

            note_label = Label(tt_frame,
                               text="Win rate fields with fewer than 200 samples are listed as 0% or NA.",
                               style="Notes.TLabel",
                               background="#3d3d3d",
                               foreground="#e6ecec",
                               anchor="c",)

            if len(self.color_dict) == 2:
                headers = {"Label": {"width": .60, "anchor": tkinter.W},
                           "Value1": {"width": .20, "anchor": tkinter.CENTER},
                           "Value2": {"width": .20, "anchor": tkinter.CENTER}}
                width = self._scale_value(340)
            else:
                headers = {"Label": {"width": .70, "anchor": tkinter.W},
                           "Value1": {"width": .30, "anchor": tkinter.CENTER}}
                width = self._scale_value(300)

            tt_width += width

            style = Style()
            style.configure("Tooltip.Treeview", rowheight=row_height)

            stats_main_table = self._create_header("tooltip_table",
                                                   tt_frame, 0, self.fonts_dict["All.TableRow"], headers, width, False, True, "Tooltip.Treeview", False)
            main_field_list = []

            values = ["Filter:"] + list(self.color_dict.keys())
            main_field_list.append(tuple(values))

            values = ["Average Taken At:"] + \
                [f"{x[constants.DATA_FIELD_ATA]}" for x in self.color_dict.values()]
            main_field_list.append(tuple(values))

            values = ["Average Last Seen At:"] + \
                [f"{x[constants.DATA_FIELD_ALSA]}" for x in self.color_dict.values()]
            main_field_list.append(tuple(values))

            values = ["Improvement When Drawn:"] + \
                [f"{x[constants.DATA_FIELD_IWD]}pp" for x in self.color_dict.values()]
            main_field_list.append(tuple(values))

            values = ["Games In Hand Win Rate:"] + \
                [f"{x[constants.DATA_FIELD_GIHWR]}%" for x in self.color_dict.values()]
            main_field_list.append(tuple(values))

            values = ["Opening Hand Win Rate:"] + \
                [f"{x[constants.DATA_FIELD_OHWR]}%" for x in self.color_dict.values()]
            main_field_list.append(tuple(values))

            values = ["Games Played Win Rate:"] + \
                [f"{x[constants.DATA_FIELD_GPWR]}%" for x in self.color_dict.values()]
            main_field_list.append(tuple(values))

            values = ["Games Drawn Win Rate:"] + \
                [f"{x[constants.DATA_FIELD_GDWR]}%" for x in self.color_dict.values()]
            main_field_list.append(tuple(values))

            values = ["Games Not Seen Win Rate:"] + \
                [f"{x[constants.DATA_FIELD_GNSWR]}%" for x in self.color_dict.values()]
            main_field_list.append(tuple(values))

            main_field_list.append(tuple(["", ""]))

            values = ["Number of Games In Hand:"] + \
                [f"{x[constants.DATA_FIELD_GIH]}" for x in self.color_dict.values()]
            main_field_list.append(tuple(values))

            values = ["Number of Games in Opening Hand:"] + \
                [f"{x[constants.DATA_FIELD_NGOH]}" for x in self.color_dict.values()]
            main_field_list.append(tuple(values))

            values = ["Number of Games Played:"] + \
                [f"{x[constants.DATA_FIELD_NGP]}" for x in self.color_dict.values()]
            main_field_list.append(tuple(values))

            values = ["Number of Games Drawn:"] + \
                [f"{x[constants.DATA_FIELD_NGD]}" for x in self.color_dict.values()]
            main_field_list.append(tuple(values))

            values = ["Number of Games Not Seen:"] + \
                [f"{x[constants.DATA_FIELD_NGND]}" for x in self.color_dict.values()]
            main_field_list.append(tuple(values))

            for x in range(2):
                main_field_list.append(tuple(["", ""]))

            stats_main_table.config(height=len(main_field_list))

            column_offset = 0
            # Add scryfall image
            if self.images_enabled:
                image_size_y = len(main_field_list) * row_height
                width = self._scale_value(280)
                size = width, image_size_y
                self.images = []
                request_header = {'User-Agent': 'Mozilla/5.0'}
                for count, picture_url in enumerate(self.image):
                    try:
                        if picture_url:
                            image_request = urllib.request.Request(
                                url=picture_url, headers=request_header)
                            raw_data = urllib.request.urlopen(
                                image_request).read()
                            im = Image.open(io.BytesIO(raw_data))
                            im.thumbnail(size, Image.ANTIALIAS)
                            image = ImageTk.PhotoImage(im)
                            image_label = Label(tt_frame, image=image)
                            image_label.grid(
                                column=count, row=1, columnspan=1)
                            self.images.append(image)
                            column_offset += 1
                            tt_width += width - self._scale_value(10)
                    except Exception as error:
                        logger.error(error)

            card_label.grid(column=0, row=0,
                            columnspan=column_offset + 2, sticky=tkinter.NSEW)

            row_count = 3
            for name, comment in self.tier_info.items():
                if not comment:
                    continue
                comment_frame = tkinter.LabelFrame(tt_frame, text=name)
                comment_frame.grid(column=0, row=row_count,
                                   columnspan=column_offset + 2, sticky=tkinter.NSEW)

                comment_label = Label(comment_frame,
                                      text=f"\"{comment}\"",
                                      background="#3d3d3d",
                                      foreground="#e6ecec",
                                      anchor="c",
                                      wraplength=tt_width,)
                comment_label.grid(column=0, row=0, sticky=tkinter.NSEW)

                font = ImageFont.truetype('times.ttf', 12)
                font_size = font.getsize(comment)
                font_rows = math.ceil(font_size[0] / tt_width) + 2
                font_height = font_rows * font_size[1]
                tt_height += self._scale_value(font_height)
                row_count += 1

            note_label.grid(column=0, row=row_count,
                            columnspan=column_offset + 2, sticky=tkinter.NSEW)

            for count, row_values in enumerate(main_field_list):
                row_tag = identify_table_row_tag(False, "", count)
                stats_main_table.insert(
                    "", index=count, iid=count, values=row_values, tag=(row_tag,))

            stats_main_table.grid(
                row=1, column=column_offset)

            tt_width += self._scale_value(10)
            location_x, location_y = identify_safe_coordinates(self.tw,
                                                               tt_width,
                                                               tt_height,
                                                               self._scale_value(
                                                                   25),
                                                               self._scale_value(20))
            self.tw.wm_geometry(f"+{location_x}+{location_y}")

            tt_frame.pack()

            self.tw.attributes("-topmost", True)
        except Exception as error:
            logger.error(error)

    def __hide_tooltip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()