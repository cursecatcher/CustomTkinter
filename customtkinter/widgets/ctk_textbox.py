import tkinter
from typing import Union, Tuple

from .ctk_canvas import CTkCanvas
from .ctk_scrollbar import CTkScrollbar
from ..theme_manager import ThemeManager
from ..draw_engine import DrawEngine
from .widget_base_class import CTkBaseClass

from .widget_helper_functions import pop_from_dict_by_set


class CTkTextbox(CTkBaseClass):
    """
    Textbox with x and y scrollbars, rounded corners, and all text features of tkinter.Text widget.
    Scrollbars only appear when they are needed. Text is wrapped on line end by default,
    set wrap='none' to disable automatic line wrapping.
    For detailed information check out the documentation.

    Detailed methods and parameters of the underlaying tkinter.Text widget can be found here:
    https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/text.html
    (most of them are implemented here too)
    """

    _scrollbar_update_time = 200  # interval in ms, to check if scrollbars are needed

    # attributes that are passed to and managed by the tkinter textbox only:
    _valid_tk_text_attributes = {"autoseparators", "cursor", "exportselection",
                                 "insertborderwidth", "insertofftime", "insertontime", "insertwidth",
                                 "maxundo", "padx", "pady", "selectborderwidth", "spacing1",
                                 "spacing2", "spacing3", "state", "tabs", "takefocus", "undo", "wrap",
                                 "xscrollcommand", "yscrollcommand"}

    def __init__(self,
                 master: any = None,
                 width: int = 200,
                 height: int = 200,
                 corner_radius: Union[int, str] = "default_theme",
                 border_width: Union[int, str] = "default_theme",
                 border_spacing: int = 3,

                 bg_color: Union[str, Tuple[str, str], None] = None,
                 fg_color: Union[str, Tuple[str, str], None] = "default_theme",
                 border_color: Union[str, Tuple[str, str]] = "default_theme",
                 text_color: Union[str, str] = "default_theme",
                 scrollbar_color: Union[str, Tuple[str, str]] = "default_theme",
                 scrollbar_hover_color:  Union[str, Tuple[str, str]] = "default_theme",

                 font: any = "default_theme",
                 activate_scrollbars: bool = True,
                 **kwargs):

        # transfer basic functionality (_bg_color, size, _appearance_mode, scaling) to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height)

        # color
        self._fg_color = ThemeManager.theme["color"]["entry"] if fg_color == "default_theme" else fg_color
        self._border_color = ThemeManager.theme["color"]["frame_border"] if border_color == "default_theme" else border_color
        self._text_color = ThemeManager.theme["color"]["text"] if text_color == "default_theme" else text_color
        self._scrollbar_color = ThemeManager.theme["color"]["scrollbar_button"] if scrollbar_color == "default_theme" else scrollbar_color
        self._scrollbar_hover_color = ThemeManager.theme["color"]["scrollbar_button_hover"] if scrollbar_hover_color == "default_theme" else scrollbar_hover_color

        # shape
        self._corner_radius = ThemeManager.theme["shape"]["frame_corner_radius"] if corner_radius == "default_theme" else corner_radius
        self._border_width = ThemeManager.theme["shape"]["frame_border_width"] if border_width == "default_theme" else border_width
        self._border_spacing = border_spacing

        # text
        self._font = (ThemeManager.theme["text"]["font"], ThemeManager.theme["text"]["size"]) if font == "default_theme" else font

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._current_width),
                                 height=self._apply_widget_scaling(self._current_height))
        self._canvas.grid(row=0, column=0, padx=0, pady=0, rowspan=2, columnspan=2, sticky="nsew")
        self._canvas.configure(bg=ThemeManager.single_color(self._bg_color, self._appearance_mode))
        self._draw_engine = DrawEngine(self._canvas)

        self._textbox = tkinter.Text(self,
                                     fg=ThemeManager.single_color(self._text_color, self._appearance_mode),
                                     width=0,
                                     height=0,
                                     font=self._apply_font_scaling(self._font),
                                     highlightthickness=0,
                                     relief="flat",
                                     insertbackground=ThemeManager.single_color(self._text_color, self._appearance_mode),
                                     bg=ThemeManager.single_color(self._fg_color, self._appearance_mode),
                                     **pop_from_dict_by_set(kwargs, self._valid_tk_text_attributes))

        self._check_kwargs_empty(kwargs, raise_error=True)

        # scrollbars
        self._scrollbars_activated = activate_scrollbars
        self._hide_x_scrollbar = True
        self._hide_y_scrollbar = True

        self._y_scrollbar = CTkScrollbar(self,
                                         width=8,
                                         height=0,
                                         border_spacing=0,
                                         fg_color=self._fg_color,
                                         scrollbar_color=self._scrollbar_color,
                                         scrollbar_hover_color=self._scrollbar_hover_color,
                                         orientation="vertical",
                                         command=self._textbox.yview)
        self._textbox.configure(yscrollcommand=self._y_scrollbar.set)

        self._x_scrollbar = CTkScrollbar(self,
                                         height=8,
                                         width=0,
                                         border_spacing=0,
                                         fg_color=self._fg_color,
                                         scrollbar_color=self._scrollbar_color,
                                         scrollbar_hover_color=self._scrollbar_hover_color,
                                         orientation="horizontal",
                                         command=self._textbox.xview)
        self._textbox.configure(xscrollcommand=self._x_scrollbar.set)

        self._create_grid_for_text_and_scrollbars(re_grid_textbox=True, re_grid_x_scrollbar=True, re_grid_y_scrollbar=True)

        self.after(50, self._check_if_scrollbars_needed)
        self._draw()

    def _create_grid_for_text_and_scrollbars(self, re_grid_textbox=False, re_grid_x_scrollbar=False, re_grid_y_scrollbar=False):

        # configure 2x2 grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0, minsize=self._apply_widget_scaling(max(self._corner_radius, self._border_width + self._border_spacing)))
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=self._apply_widget_scaling(max(self._corner_radius, self._border_width + self._border_spacing)))

        if re_grid_textbox:
            self._textbox.grid(row=0, column=0, rowspan=1, columnspan=1, sticky="nsew",
                               padx=(self._apply_widget_scaling(max(self._corner_radius, self._border_width + self._border_spacing)), 0),
                               pady=(self._apply_widget_scaling(max(self._corner_radius, self._border_width + self._border_spacing)), 0))

        if re_grid_x_scrollbar:
            if not self._hide_x_scrollbar and self._scrollbars_activated:
                self._x_scrollbar.grid(row=1, column=0, rowspan=1, columnspan=1, sticky="ewn",
                                       pady=(3, self._border_spacing + self._border_width),
                                       padx=(max(self._corner_radius, self._border_width + self._border_spacing), 0))  # scrollbar grid method without scaling
            else:
                self._x_scrollbar.grid_forget()

        if re_grid_y_scrollbar:
            if not self._hide_y_scrollbar and self._scrollbars_activated:
                self._y_scrollbar.grid(row=0, column=1, rowspan=1, columnspan=1, sticky="nsw",
                                       padx=(3, self._border_spacing + self._border_width),
                                       pady=(max(self._corner_radius, self._border_width + self._border_spacing), 0))  # scrollbar grid method without scaling
            else:
                self._y_scrollbar.grid_forget()

    def _check_if_scrollbars_needed(self, event=None, continue_loop: bool = True):
        """ Method hides or places the scrollbars if they are needed on key release event of tkinter.text widget """

        if self._scrollbars_activated:
            if self._textbox.xview() != (0.0, 1.0) and not self._x_scrollbar.winfo_ismapped():  # x scrollbar needed
                self._hide_x_scrollbar = False
                self._create_grid_for_text_and_scrollbars(re_grid_x_scrollbar=True)
            elif self._textbox.xview() == (0.0, 1.0) and self._x_scrollbar.winfo_ismapped():  # x scrollbar not needed
                self._hide_x_scrollbar = True
                self._create_grid_for_text_and_scrollbars(re_grid_x_scrollbar=True)

            if self._textbox.yview() != (0.0, 1.0) and not self._y_scrollbar.winfo_ismapped():  # y scrollbar needed
                self._hide_y_scrollbar = False
                self._create_grid_for_text_and_scrollbars(re_grid_y_scrollbar=True)
            elif self._textbox.yview() == (0.0, 1.0) and self._y_scrollbar.winfo_ismapped():  # y scrollbar not needed
                self._hide_y_scrollbar = True
                self._create_grid_for_text_and_scrollbars(re_grid_y_scrollbar=True)
        else:
            self._hide_x_scrollbar = False
            self._hide_x_scrollbar = False
            self._create_grid_for_text_and_scrollbars(re_grid_y_scrollbar=True)

        if self._textbox.winfo_exists() and continue_loop is True:
            self.after(self._scrollbar_update_time, lambda: self._check_if_scrollbars_needed(continue_loop=True))

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

        self._textbox.configure(font=self._apply_font_scaling(self._font))
        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._create_grid_for_text_and_scrollbars(re_grid_textbox=False, re_grid_x_scrollbar=True, re_grid_y_scrollbar=True)
        self._draw()

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    def _draw(self, no_color_updates=False):

        if not self._canvas.winfo_exists():
            return

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(self._apply_widget_scaling(self._current_width),
                                                                              self._apply_widget_scaling(self._current_height),
                                                                              self._apply_widget_scaling(self._corner_radius),
                                                                              self._apply_widget_scaling(self._border_width))

        if no_color_updates is False or requires_recoloring:
            if self._fg_color is None:
                self._canvas.itemconfig("inner_parts",
                                        fill=ThemeManager.single_color(self._bg_color, self._appearance_mode),
                                        outline=ThemeManager.single_color(self._bg_color, self._appearance_mode))
                self._textbox.configure(fg=ThemeManager.single_color(self._text_color, self._appearance_mode),
                                        bg=ThemeManager.single_color(self._bg_color, self._appearance_mode),
                                        insertbackground=ThemeManager.single_color(self._text_color, self._appearance_mode))
                self._x_scrollbar.configure(fg_color=self._bg_color, scrollbar_color=self._scrollbar_color,
                                            scrollbar_hover_color=self._scrollbar_hover_color)
                self._y_scrollbar.configure(fg_color=self._bg_color, scrollbar_color=self._scrollbar_color,
                                            scrollbar_hover_color=self._scrollbar_hover_color)
            else:
                self._canvas.itemconfig("inner_parts",
                                        fill=ThemeManager.single_color(self._fg_color, self._appearance_mode),
                                        outline=ThemeManager.single_color(self._fg_color, self._appearance_mode))
                self._textbox.configure(fg=ThemeManager.single_color(self._text_color, self._appearance_mode),
                                        bg=ThemeManager.single_color(self._fg_color, self._appearance_mode),
                                        insertbackground=ThemeManager.single_color(self._text_color, self._appearance_mode))
                self._x_scrollbar.configure(fg_color=self._fg_color, scrollbar_color=self._scrollbar_color,
                                            scrollbar_hover_color=self._scrollbar_hover_color)
                self._y_scrollbar.configure(fg_color=self._fg_color, scrollbar_color=self._scrollbar_color,
                                            scrollbar_hover_color=self._scrollbar_hover_color)

            self._canvas.itemconfig("border_parts",
                                    fill=ThemeManager.single_color(self._border_color, self._appearance_mode),
                                    outline=ThemeManager.single_color(self._border_color, self._appearance_mode))
            self._canvas.configure(bg=ThemeManager.single_color(self._bg_color, self._appearance_mode))

        self._canvas.tag_lower("inner_parts")
        self._canvas.tag_lower("border_parts")

    def configure(self, require_redraw=False, **kwargs):
        if "fg_color" in kwargs:
            self._fg_color = kwargs.pop("fg_color")
            require_redraw = True

            # check if CTk widgets are children of the frame and change their _bg_color to new frame fg_color
            for child in self.winfo_children():
                if isinstance(child, CTkBaseClass) and hasattr(child, "_fg_color"):
                    child.configure(bg_color=self._fg_color)

        if "border_color" in kwargs:
            self._border_color = kwargs.pop("border_color")
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            require_redraw = True

        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            self._create_grid_for_text_and_scrollbars(re_grid_textbox=True, re_grid_x_scrollbar=True, re_grid_y_scrollbar=True)
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            self._create_grid_for_text_and_scrollbars(re_grid_textbox=True, re_grid_x_scrollbar=True, re_grid_y_scrollbar=True)
            require_redraw = True

        if "border_spacing" in kwargs:
            self._border_spacing = kwargs.pop("border_spacing")
            self._create_grid_for_text_and_scrollbars(re_grid_textbox=True, re_grid_x_scrollbar=True, re_grid_y_scrollbar=True)
            require_redraw = True

        if "font" in kwargs:
            self._font = kwargs.pop("font")
            self._textbox.configure(font=self._apply_font_scaling(self._font))

        self._textbox.configure(**pop_from_dict_by_set(kwargs, self._valid_tk_text_attributes))
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> any:
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_width":
            return self._border_width
        elif attribute_name == "border_spacing":
            return self._border_spacing

        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "text_color":
            return self._text_color

        elif attribute_name == "font":
            return self._font

        else:
            return super().cget(attribute_name)

    def bind(self, sequence=None, command=None, add=None):
        """ called on the tkinter.Text """

        # if sequence is <KeyRelease>, allow only to add the binding to keep the _textbox_modified_event() being called
        if sequence == "<KeyRelease>":
            return self._textbox.bind(sequence, command, add="+")
        else:
            return self._textbox.bind(sequence, command, add)

    def unbind(self, sequence, funcid=None):
        """ called on the tkinter.Text """
        return self._textbox.unbind(sequence, funcid)

    def focus(self):
        return self._textbox.focus()

    def focus_set(self):
        return self._textbox.focus_set()

    def focus_force(self):
        return self._textbox.focus_force()

    def insert(self, index, text, tags=None):
        self._check_if_scrollbars_needed()
        return self._textbox.insert(index, text, tags)

    def get(self, index1, index2=None):
        return self._textbox.get(index1, index2)

    def bbox(self, index):
        return self._textbox.bbox(index)

    def compare(self, index, op, index2):
        return self._textbox.compare(index, op, index2)

    def delete(self, index1, index2=None):
        return self._textbox.delete(index1, index2)

    def dlineinfo(self, index):
        return self._textbox.dlineinfo(index)

    def edit_modified(self, arg=None):
        return self._textbox.edit_modified(arg)

    def edit_redo(self):
        self._check_if_scrollbars_needed()
        return self._textbox.edit_redo()

    def edit_reset(self):
        return self._textbox.edit_reset()

    def edit_separator(self):
        return self._textbox.edit_separator()

    def edit_undo(self):
        self._check_if_scrollbars_needed()
        return self._textbox.edit_undo()

    def image_create(self, index, **kwargs):
        raise AttributeError("embedding images is forbidden, because would be incompatible with scaling")

    def image_cget(self, index, option):
        raise AttributeError("embedding images is forbidden, because would be incompatible with scaling")

    def image_configure(self, index):
        raise AttributeError("embedding images is forbidden, because would be incompatible with scaling")

    def image_names(self):
        raise AttributeError("embedding images is forbidden, because would be incompatible with scaling")

    def index(self, i):
        return self._textbox.index(i)

    def mark_gravity(self, mark, gravity=None):
        return self._textbox.mark_gravity(mark, gravity)

    def mark_names(self):
        return self._textbox.mark_names()

    def mark_next(self, index):
        return self._textbox.mark_next(index)

    def mark_previous(self, index):
        return self._textbox.mark_previous(index)

    def mark_set(self, mark, index):
        return self._textbox.mark_set(mark, index)

    def mark_unset(self, mark):
        return self._textbox.mark_unset(mark)

    def scan_dragto(self, x, y):
        return self._textbox.scan_dragto(x, y)

    def scan_mark(self, x, y):
        return self._textbox.scan_mark(x, y)

    def search(self, pattern, index, *args, **kwargs):
        return self._textbox.search(pattern, index, *args, **kwargs)

    def see(self, index):
        return self._textbox.see(index)

    def tag_add(self, tagName, index1, index2=None):
        return self._textbox.tag_add(tagName, index1, index2)

    def tag_bind(self, tagName, sequence, func, add=None):
        return self._textbox.tag_bind(tagName, sequence, func, add)

    def tag_cget(self, tagName, option):
        return self._textbox.tag_cget(tagName, option)

    def tag_config(self, tagName, **kwargs):
        if "font" in kwargs:
            raise AttributeError("'font' option forbidden, because would be incompatible with scaling")
        return self._textbox.tag_config(tagName, **kwargs)

    def tag_delete(self, *tagName):
        return self._textbox.tag_delete(*tagName)

    def tag_lower(self, tagName, belowThis=None):
        return self._textbox.tag_lower(tagName, belowThis)

    def tag_names(self, index=None):
        return self._textbox.tag_names(index)

    def tag_nextrange(self, tagName, index1, index2=None):
        return self._textbox.tag_nextrange(tagName, index1, index2)

    def tag_prevrange(self, tagName, index1, index2=None):
        return self._textbox.tag_prevrange(tagName, index1, index2)

    def tag_raise(self, tagName, aboveThis=None):
        return self._textbox.tag_raise(tagName, aboveThis)

    def tag_ranges(self, tagName):
        return self._textbox.tag_ranges(tagName)

    def tag_remove(self, tagName, index1, index2=None):
        return self._textbox.tag_remove(tagName, index1, index2)

    def tag_unbind(self, tagName, sequence, funcid=None):
        return self._textbox.tag_unbind(tagName, sequence, funcid)

    def window_cget(self, index, option):
        raise AttributeError("embedding widgets is forbidden, would probably cause all kinds of problems ;)")

    def window_configure(self, index, option):
        raise AttributeError("embedding widgets is forbidden, would probably cause all kinds of problems ;)")

    def window_create(self, index, **kwargs):
        raise AttributeError("embedding widgets is forbidden, would probably cause all kinds of problems ;)")

    def window_names(self):
        raise AttributeError("embedding widgets is forbidden, would probably cause all kinds of problems ;)")

    def xview(self, *args):
        return self._textbox.xview(*args)

    def xview_moveto(self, fraction):
        return self._textbox.xview_moveto(fraction)

    def xview_scroll(self, n, what):
        return self._textbox.xview_scroll(n, what)

    def yview(self, *args):
        return self._textbox.yview(*args)

    def yview_moveto(self, fraction):
        return self._textbox.yview_moveto(fraction)

    def yview_scroll(self, n, what):
        return self._textbox.yview_scroll(n, what)
