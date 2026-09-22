"""
Uiverse-inspired Animated Combobox for PrayerMusicGuard
Based on Uiverse.io by Harsha2lucky
Adapted for dark/light theme support and searchable country/city selection.
"""

import tkinter as tk
from tkinter import ttk
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Callable


class UiverseCombobox(tk.Frame):
    """
    A custom combobox with Uiverse-inspired animation:
    - Collapsed circular input appearance
    - Smooth expansion on focus
    - Caret animation
    - Searchable dropdown
    - Theme-aware (dark/light)
    """

    def __init__(
        self,
        parent,
        variable: tk.StringVar,
        items: List[Dict[str, str]],
        display_key: str = "name_ar",
        value_key: str = "code",
        placeholder: str = "",
        width: int = 300,
        on_select: Optional[Callable[[str, Dict], None]] = None,
        theme: str = "dark",
        disabled: bool = False,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.variable = variable
        self.items = items
        self.display_key = display_key
        self.value_key = value_key
        self.placeholder = placeholder
        self.target_width = width
        self.on_select = on_select
        self.theme = theme
        self.disabled = disabled

        # State
        self._expanded = False
        self._focused = False
        self._dropdown_visible = False
        self._filtered_items = items
        self._selected_index = -1
        self._animating = False
        self._animation_start = 0
        self._animation_duration = 300  # ms

        # Theme colors
        self._update_theme_colors()

        self._build_ui()
        self._bind_events()

        # Set initial value if variable has one
        if self.variable.get():
            self._set_display_from_value(self.variable.get())

    def _update_theme_colors(self):
        """Update colors based on current theme."""
        if self.theme == "dark":
            self.colors = {
                "bg": "#29292D",
                "surface": "#2D2D30",
                "surface_alt": "#3D3D42",
                "border": "#3D3D42",
                "border_focus": "#4A90E2",
                "text": "#FFFFFF",
                "muted": "#A0A0A0",
                "accent": "#4A90E2",
                "accent_hover": "#6BB0FF",
                "dropdown_bg": "#2D2D30",
                "dropdown_hover": "#3D3D42",
                "dropdown_selected": "#4A90E2",
                "caret": "#4A90E2",
                "placeholder": "#6D6D70",
                "shadow": "#00000080",
            }
        else:
            self.colors = {
                "bg": "#FFFFFF",
                "surface": "#F2F2F7",
                "surface_alt": "#E5E5EA",
                "border": "#D1D1D6",
                "border_focus": "#0078D4",
                "text": "#000000",
                "muted": "#6D6D70",
                "accent": "#0078D4",
                "accent_hover": "#106EBE",
                "dropdown_bg": "#FFFFFF",
                "dropdown_hover": "#F0F0F0",
                "dropdown_selected": "#0078D4",
                "caret": "#0078D4",
                "placeholder": "#A0A0A0",
                "shadow": "#0000001A",
            }

    def set_theme(self, theme: str):
        """Update theme and refresh UI."""
        self.theme = theme
        self._update_theme_colors()
        self._redraw()

    def _build_ui(self):
        """Build the combobox UI components."""
        self.configure(background=self.colors["bg"])

        # Main container frame
        self.container = tk.Frame(self, background=self.colors["bg"])
        self.container.pack(fill="x", expand=True)

        # Input frame (the animated part)
        self.input_frame = tk.Frame(self.container, background=self.colors["bg"])
        self.input_frame.pack(fill="x", expand=True)

        # Canvas for the animated background/border
        self.canvas = tk.Canvas(
            self.input_frame,
            height=44,
            highlightthickness=0,
            bd=0,
            background=self.colors["bg"]
        )
        self.canvas.pack(fill="x", expand=True)

        # The actual entry widget (hidden initially, shown when expanded)
        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            self.input_frame,
            textvariable=self.entry_var,
            font=("Segoe UI", 11),
            bd=0,
            highlightthickness=0,
            relief="flat",
            insertbackground=self.colors["accent"],
            background=self.colors["surface"],
            foreground=self.colors["text"],
            disabledbackground=self.colors["surface_alt"],
            disabledforeground=self.colors["muted"]
        )
        self.entry.place(x=0, y=0, width=0, height=0)  # Hidden initially

        # Display label (shown when collapsed)
        self.display_label = tk.Label(
            self.input_frame,
            text=self.placeholder,
            font=("Segoe UI", 11),
            background=self.colors["bg"],
            foreground=self.colors["placeholder"],
            anchor="e",
            padx=16
        )
        self.display_label.place(x=0, y=0, relwidth=1, height=44)

        # Caret/handle indicator (the animated circle/line)
        self.caret_canvas = tk.Canvas(
            self.input_frame,
            width=28,
            height=44,
            highlightthickness=0,
            bd=0,
            background=self.colors["bg"]
        )
        self.caret_canvas.place(relx=1.0, x=-28, y=0, anchor="ne")

        # Dropdown listbox frame (initially hidden)
        self.dropdown_frame = tk.Frame(
            self,
            background=self.colors["dropdown_bg"],
            bd=1,
            relief="solid",
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        # Don't pack yet - will show on focus

        # Dropdown canvas with scrollbar
        self.dropdown_canvas = tk.Canvas(
            self.dropdown_frame,
            background=self.colors["dropdown_bg"],
            highlightthickness=0,
            bd=0
        )
        self.dropdown_scrollbar = ttk.Scrollbar(
            self.dropdown_frame,
            orient="vertical",
            command=self.dropdown_canvas.yview
        )
        self.dropdown_canvas.configure(yscrollcommand=self.dropdown_scrollbar.set)

        self.dropdown_scrollbar.pack(side="right", fill="y")
        self.dropdown_canvas.pack(side="left", fill="both", expand=True)

        # Inner frame for items
        self.dropdown_inner = tk.Frame(self.dropdown_canvas, background=self.colors["dropdown_bg"])
        self.dropdown_window = self.dropdown_canvas.create_window(
            (0, 0), window=self.dropdown_inner, anchor="nw"
        )

        self.dropdown_inner.bind("<Configure>", self._on_dropdown_configure)
        self.dropdown_canvas.bind("<Configure>", self._on_canvas_configure)

        # Item labels storage
        self.item_labels = []

        # Bind mouse wheel for dropdown scrolling
        self.dropdown_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.dropdown_canvas.bind("<Button-4>", self._on_mousewheel)
        self.dropdown_canvas.bind("<Button-5>", self._on_mousewheel)

        # Initial draw
        self._draw_collapsed()

    def _bind_events(self):
        """Bind all necessary events."""
        # Focus events on the input frame
        self.input_frame.bind("<FocusIn>", self._on_focus_in)
        self.input_frame.bind("<FocusOut>", self._on_focus_out)
        self.input_frame.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Button-1>", self._on_click)
        self.display_label.bind("<Button-1>", self._on_click)
        self.caret_canvas.bind("<Button-1>", self._on_click)

        # Entry events
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<KeyRelease>", self._on_entry_key)
        self.entry.bind("<Down>", self._on_entry_down)
        self.entry.bind("<Up>", self._on_entry_up)
        self.entry.bind("<Return>", self._on_entry_return)
        self.entry.bind("<Escape>", self._on_entry_escape)

        # Dropdown item events will be bound per item

        # Global click to close dropdown
        self.winfo_toplevel().bind("<Button-1>", self._on_global_click, add="+")

    def _on_global_click(self, event):
        """Close dropdown when clicking outside."""
        widget = event.widget
        while widget:
            if widget == self or widget == self.dropdown_frame:
                return
            widget = widget.master
        self._collapse()

    def _on_focus_in(self, event):
        """Handle focus in - expand the combobox."""
        if self.disabled:
            return
        self._focused = True
        self._expand()

    def _on_focus_out(self, event):
        """Handle focus out - collapse after delay."""
        if self.disabled:
            return
        # Check if focus moved to dropdown or entry
        self.root.after(100, self._check_focus_lost)

    def _check_focus_lost(self):
        """Check if focus truly left the combobox."""
        focused = self.root.focus_get()
        if focused not in (self.entry, self.dropdown_canvas, self.dropdown_inner, *self.item_labels):
            self._focused = False
            if not self._dropdown_visible:
                self._collapse()

    def _on_click(self, event):
        """Handle click on collapsed/expanded input."""
        if self.disabled:
            return
        if not self._expanded:
            self.entry.focus_set()
        else:
            self.entry.focus_set()

    def _on_entry_key(self, event):
        """Handle typing in entry - filter items."""
        query = self.entry_var.get().lower()
        self._filter_items(query)
        if not self._dropdown_visible:
            self._show_dropdown()

    def _on_entry_down(self, event):
        """Handle down arrow - navigate dropdown."""
        if self.item_labels:
            self._selected_index = min(self._selected_index + 1, len(self.item_labels) - 1)
            self._update_selection()
            self._ensure_visible(self._selected_index)

    def _on_entry_up(self, event):
        """Handle up arrow - navigate dropdown."""
        if self.item_labels:
            self._selected_index = max(self._selected_index - 1, 0)
            self._update_selection()
            self._ensure_visible(self._selected_index)

    def _on_entry_return(self, event):
        """Handle Enter - select current item."""
        if 0 <= self._selected_index < len(self._filtered_items):
            self._select_item(self._filtered_items[self._selected_index])
        self._collapse()

    def _on_entry_escape(self, event):
        """Handle Escape - collapse without selection."""
        self._collapse()

    def _expand(self):
        """Animate expansion from collapsed circle to full input."""
        if self._expanded or self._animating:
            return
        self._animating = True
        self._animation_start = self.root.tk.call("clock", "milliseconds")
        self._animate_expand()

    def _animate_expand(self):
        """Animate the expansion."""
        now = self.root.tk.call("clock", "milliseconds")
        elapsed = now - self._animation_start
        progress = min(1.0, elapsed / self._animation_duration)

        # Ease out cubic
        progress = 1 - (1 - progress) ** 3

        # Calculate widths
        start_width = 44  # Circle diameter
        end_width = self.target_width
        current_width = int(start_width + (end_width - start_width) * progress)

        # Update canvas width
        self.canvas.configure(width=current_width)

        # Move caret canvas
        self.caret_canvas.place(relx=1.0, x=-28, y=0, anchor="ne")

        # Show entry when halfway
        if progress > 0.5 and not self.entry.winfo_ismapped():
            self.entry.place(x=16, y=8, width=current_width - 52, height=28)
            self.entry_var.set(self.display_label.cget("text") if self.display_label.cget("text") != self.placeholder else "")
            self.display_label.configure(text="")
            self.entry.focus_set()
            self.entry.icursor(tk.END)

        # Draw animated border/background
        self._draw_expanding(progress, current_width)

        if progress < 1.0:
            self.root.after(16, self._animate_expand)
        else:
            self._animating = False
            self._expanded = True
            self._draw_expanded()
            self._show_dropdown()

    def _draw_collapsed(self):
        """Draw the collapsed circular state."""
        self.canvas.delete("all")
        w = 44
        h = 44
        cx, cy = w // 2, h // 2
        r = 20

        # Outer ring
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=self.colors["border"], width=2, fill=self.colors["bg"]
        )

        # Caret handle (circle at right)
        handle_x = cx + r - 4
        self.caret_canvas.delete("all")
        self.caret_canvas.create_oval(
            handle_x - 10, cy - 10, handle_x + 10, cy + 10,
            fill=self.colors["caret"], outline=""
        )

    def _draw_expanding(self, progress: float, width: int):
        """Draw during expansion animation."""
        self.canvas.delete("all")
        h = 44

        # Background rect with rounded corners (approximated)
        r = int(22 * (1 - progress) + 6 * progress)
        self._draw_rounded_rect(self.canvas, 2, 2, width - 2, h - 2, r,
                                fill=self.colors["surface"],
                                outline=self.colors["border_focus"] if progress > 0.5 else self.colors["border"],
                                width=2)

        # Caret animation - moves from right to left, transforms from circle to line
        self.caret_canvas.delete("all")
        cx_start = width - 14
        cx_end = 14
        cx = cx_start + (cx_end - cx_start) * progress
        cy = h // 2

        if progress < 0.3:
            # Circle shrinking
            r_handle = int(10 * (1 - progress / 0.3))
            self.caret_canvas.create_oval(
                cx - r_handle, cy - r_handle, cx + r_handle, cy + r_handle,
                fill=self.colors["caret"], outline=""
            )
        else:
            # Vertical line (caret)
            line_h = int(20 * min(1.0, (progress - 0.3) / 0.3))
            self.caret_canvas.create_line(
                cx, cy - line_h // 2, cx, cy + line_h // 2,
                fill=self.colors["caret"], width=2, capstyle="round"
            )

    def _draw_expanded(self):
        """Draw the fully expanded state."""
        self.canvas.delete("all")
        w = self.target_width
        h = 44
        r = 6

        self._draw_rounded_rect(self.canvas, 2, 2, w - 2, h - 2, r,
                                fill=self.colors["surface"],
                                outline=self.colors["border_focus"],
                                width=2)

        # Caret as blinking line
        self.caret_canvas.delete("all")
        cx = 14
        cy = h // 2
        self.caret_canvas.create_line(
            cx, cy - 10, cx, cy + 10,
            fill=self.colors["caret"], width=2, capstyle="round"
        )

    def _collapse(self):
        """Animate collapse back to circle."""
        if not self._expanded or self._animating:
            return
        self._animating = True
        self._animation_start = self.root.tk.call("clock", "milliseconds")
        self._animate_collapse()

    def _animate_collapse(self):
        """Animate the collapse."""
        now = self.root.tk.call("clock", "milliseconds")
        elapsed = now - self._animation_start
        progress = min(1.0, elapsed / self._animation_duration)

        # Ease in cubic
        progress = progress ** 3

        # Calculate widths
        start_width = self.target_width
        end_width = 44
        current_width = int(start_width + (end_width - start_width) * progress)

        # Hide entry early
        if progress > 0.3:
            self.entry.place_forget()
            display_text = self.entry_var.get() or self.placeholder
            self.display_label.configure(
                text=display_text,
                foreground=self.colors["text"] if self.entry_var.get() else self.colors["placeholder"]
            )

        # Update canvas width
        self.canvas.configure(width=current_width)
        self.caret_canvas.place(relx=1.0, x=-28, y=0, anchor="ne")

        # Draw collapsing
        self._draw_collapsing(progress, current_width)

        if progress < 1.0:
            self.root.after(16, self._animate_collapse)
        else:
            self._animating = False
            self._expanded = False
            self._hide_dropdown()
            self._draw_collapsed()

    def _draw_collapsing(self, progress: float, width: int):
        """Draw during collapse animation."""
        self.canvas.delete("all")
        h = 44

        r = int(6 + (22 - 6) * progress)
        self._draw_rounded_rect(self.canvas, 2, 2, width - 2, h - 2, r,
                                fill=self.colors["surface"] if progress < 0.5 else self.colors["bg"],
                                outline=self.colors["border_focus"] if progress < 0.5 else self.colors["border"],
                                width=2)

        # Caret animation reverse
        self.caret_canvas.delete("all")
        cx_start = 14
        cx_end = width - 14
        cx = cx_start + (cx_end - cx_start) * progress
        cy = h // 2

        if progress > 0.7:
            # Circle growing
            r_handle = int(10 * (progress - 0.7) / 0.3)
            self.caret_canvas.create_oval(
                cx - r_handle, cy - r_handle, cx + r_handle, cy + r_handle,
                fill=self.colors["caret"], outline=""
            )
        else:
            # Vertical line shrinking
            line_h = int(20 * (1 - progress / 0.7))
            self.caret_canvas.create_line(
                cx, cy - line_h // 2, cx, cy + line_h // 2,
                fill=self.colors["caret"], width=2, capstyle="round"
            )

    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
        """Draw a rounded rectangle on canvas."""
        r = max(2, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
        pts = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1
        ]
        return canvas.create_polygon(pts, smooth=True, **kwargs)

    def _show_dropdown(self):
        """Show the dropdown with filtered items."""
        if self._dropdown_visible or not self._filtered_items:
            return

        self._build_dropdown_items()
        self._dropdown_visible = True

        # Position dropdown below input
        self.update_idletasks()
        x = self.input_frame.winfo_rootx() - self.winfo_rootx()
        y = self.input_frame.winfo_rooty() - self.winfo_rooty() + 44 + 4

        self.dropdown_frame.place(x=x, y=y, width=self.target_width)

        # Calculate height (max 10 items)
        item_height = 36
        visible_items = min(len(self._filtered_items), 10)
        height = visible_items * item_height + 2
        self.dropdown_frame.configure(height=height)
        self.dropdown_canvas.configure(height=height, width=self.target_width - 20)

        # Bring to front
        self.dropdown_frame.lift()

    def _hide_dropdown(self):
        """Hide the dropdown."""
        self._dropdown_visible = False
        self.dropdown_frame.place_forget()

    def _build_dropdown_items(self):
        """Build dropdown item labels."""
        # Clear existing
        for label in self.item_labels:
            label.destroy()
        self.item_labels.clear()

        # Create new labels
        for idx, item in enumerate(self._filtered_items):
            display_text = item.get(self.display_key, item.get(self.value_key, ""))
            label = tk.Label(
                self.dropdown_inner,
                text=display_text,
                font=("Segoe UI", 10),
                background=self.colors["dropdown_bg"],
                foreground=self.colors["text"],
                anchor="e",
                padx=16,
                pady=8,
                cursor="hand2"
            )
            label.pack(fill="x")
            label.bind("<Button-1>", lambda e, i=item: self._select_item(i))
            label.bind("<Enter>", lambda e, l=label: self._on_item_hover(l, True))
            label.bind("<Leave>", lambda e, l=label: self._on_item_hover(l, False))
            self.item_labels.append(label)

        self._selected_index = -1
        self._update_selection()

        # Update scroll region
        self.dropdown_inner.update_idletasks()
        self.dropdown_canvas.configure(scrollregion=self.dropdown_canvas.bbox("all"))

    def _on_item_hover(self, label, entering):
        """Handle item hover."""
        if entering:
            label.configure(background=self.colors["dropdown_hover"])
        else:
            label.configure(background=self.colors["dropdown_bg"])

    def _update_selection(self):
        """Update visual selection in dropdown."""
        for idx, label in enumerate(self.item_labels):
            if idx == self._selected_index:
                label.configure(
                    background=self.colors["dropdown_selected"],
                    foreground=self.colors["bg"] if self.theme == "dark" else "#FFFFFF"
                )
            else:
                label.configure(
                    background=self.colors["dropdown_bg"],
                    foreground=self.colors["text"]
                )

    def _ensure_visible(self, index):
        """Ensure selected item is visible in scroll view."""
        if not self.item_labels:
            return
        label = self.item_labels[index]
        self.dropdown_canvas.update_idletasks()
        label_y = label.winfo_y()
        label_h = label.winfo_height()
        canvas_h = self.dropdown_canvas.winfo_height()
        scroll_top = self.dropdown_canvas.canvasy(0)

        if label_y < scroll_top:
            self.dropdown_canvas.yview_scroll(-1, "units")
        elif label_y + label_h > scroll_top + canvas_h:
            self.dropdown_canvas.yview_scroll(1, "units")

    def _filter_items(self, query: str):
        """Filter items based on search query."""
        if not query:
            self._filtered_items = self.items
        else:
            self._filtered_items = [
                item for item in self.items
                if query in item.get(self.display_key, "").lower()
                or query in item.get("name_en", "").lower()
                or query in item.get(self.value_key, "").lower()
            ]
        if self._dropdown_visible:
            self._build_dropdown_items()

    def _select_item(self, item: Dict):
        """Select an item and update variable."""
        value = item.get(self.value_key, "")
        display = item.get(self.display_key, item.get(self.value_key, ""))

        self.variable.set(value)
        self.entry_var.set(display)
        self.display_label.configure(text=display, foreground=self.colors["text"])

        if self.on_select:
            self.on_select(value, item)

    def _set_display_from_value(self, value: str):
        """Set display label from value (for initial load)."""
        for item in self.items:
            if item.get(self.value_key) == value:
                display = item.get(self.display_key, item.get(self.value_key, ""))
                self.display_label.configure(text=display, foreground=self.colors["text"])
                self.entry_var.set(display)
                return
        # Value not in list - show as-is
        self.display_label.configure(text=value, foreground=self.colors["text"])
        self.entry_var.set(value)

    def _on_dropdown_configure(self, event):
        """Handle dropdown inner frame configure."""
        self.dropdown_canvas.configure(scrollregion=self.dropdown_canvas.bbox("all"))
        self.dropdown_canvas.itemconfigure(self.dropdown_window, width=event.width)

    def _on_canvas_configure(self, event):
        """Handle dropdown canvas configure."""
        self.dropdown_canvas.itemconfigure(self.dropdown_window, width=event.width)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        if event.num == 4 or event.delta > 0:
            self.dropdown_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.dropdown_canvas.yview_scroll(1, "units")

    def _redraw(self):
        """Redraw the component with current theme."""
        self.configure(background=self.colors["bg"])
        self.container.configure(background=self.colors["bg"])
        self.input_frame.configure(background=self.colors["bg"])
        self.canvas.configure(background=self.colors["bg"])
        self.caret_canvas.configure(background=self.colors["bg"])
        self.display_label.configure(background=self.colors["bg"])
        self.dropdown_frame.configure(background=self.colors["dropdown_bg"],
                                       highlightbackground=self.colors["border"])
        self.dropdown_canvas.configure(background=self.colors["dropdown_bg"])
        self.dropdown_inner.configure(background=self.colors["dropdown_bg"])

        self.entry.configure(
            background=self.colors["surface"],
            foreground=self.colors["text"],
            insertbackground=self.colors["accent"],
            disabledbackground=self.colors["surface_alt"],
            disabledforeground=self.colors["muted"]
        )

        if self._expanded:
            self._draw_expanded()
        else:
            self._draw_collapsed()

        for label in self.item_labels:
            label.configure(
                background=self.colors["dropdown_bg"],
                foreground=self.colors["text"]
            )

    def set_items(self, items: List[Dict]):
        """Update the items list."""
        self.items = items
        self._filtered_items = items
        if self._dropdown_visible:
            self._build_dropdown_items()

    def set_enabled(self, enabled: bool):
        """Enable or disable the combobox."""
        self.disabled = not enabled
        if enabled:
            self.entry.configure(state="normal")
            self.display_label.configure(foreground=self.colors["text"] if self.variable.get() else self.colors["placeholder"])
        else:
            self.entry.configure(state="disabled")
            self.display_label.configure(foreground=self.colors["muted"])
        self._redraw()

    def get_selected_item(self) -> Optional[Dict]:
        """Get the currently selected item dict."""
        value = self.variable.get()
        for item in self.items:
            if item.get(self.value_key) == value:
                return item
        return None


class CountryCitySelector(tk.Frame):
    """
    Combined Country + City selector with Uiverse-style comboboxes.
    Handles the dependency: city selector activates only after country selection.
    """

    def __init__(
        self,
        parent,
        country_var: tk.StringVar,
        city_var: tk.StringVar,
        on_country_change: Optional[Callable[[str], None]] = None,
        on_city_change: Optional[Callable[[str], None]] = None,
        theme: str = "dark",
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.country_var = country_var
        self.city_var = city_var
        self.on_country_change = on_country_change
        self.on_city_change = on_city_change
        self.theme = theme

        # Load data
        self.countries = self._load_countries()
        self.cities_data = self._load_cities()

        # Current state
        self.current_country_code = ""
        self.country_combo = None
        self.city_combo = None

        self._build_ui()
        self._bind_variables()

        # Set initial values if present (defer to avoid callback during init)
        self.after_idle(self._init_values)

    def _load_countries(self) -> List[Dict]:
        """Load countries from JSON file."""
        try:
            data_path = Path(__file__).parent / "assets" / "data" / "countries.json"
            if data_path.exists():
                with open(data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Failed to load countries: {e}")
        return []

    def _load_cities(self) -> Dict[str, List[str]]:
        """Load cities from JSON file."""
        try:
            data_path = Path(__file__).parent / "assets" / "data" / "cities.json"
            if data_path.exists():
                with open(data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Failed to load cities: {e}")
        return {}

    def _build_ui(self):
        """Build the country and city selector UI."""
        self.configure(background=self._get_bg_color())

        # Country selector
        country_frame = tk.Frame(self, background=self._get_bg_color())
        country_frame.pack(fill="x", pady=(0, 8))

        tk.Label(
            country_frame,
            text="الدولة:",
            font=("Segoe UI", 10, "bold"),
            background=self._get_bg_color(),
            foreground=self._get_text_color()
        ).pack(side="right", padx=(0, 8))

        self.country_combo = UiverseCombobox(
            country_frame,
            variable=self.country_var,
            items=self.countries,
            display_key="name_ar",
            value_key="code",
            placeholder="اختر الدولة",
            width=280,
            on_select=self._on_country_selected,
            theme=self.theme
        )
        self.country_combo.pack(side="right", fill="x", expand=True)

        # City selector
        city_frame = tk.Frame(self, background=self._get_bg_color())
        city_frame.pack(fill="x")

        tk.Label(
            city_frame,
            text="المدينة:",
            font=("Segoe UI", 10, "bold"),
            background=self._get_bg_color(),
            foreground=self._get_text_color()
        ).pack(side="right", padx=(0, 8))

        self.city_combo = UiverseCombobox(
            city_frame,
            variable=self.city_var,
            items=[],  # Will be populated after country selection
            display_key="name",
            value_key="name",
            placeholder="اختر المدينة",
            width=280,
            on_select=self._on_city_selected,
            theme=self.theme,
            disabled=True
        )
        self.city_combo.pack(side="right", fill="x", expand=True)

    def _get_bg_color(self):
        return "#29292D" if self.theme == "dark" else "#FFFFFF"

    def _get_text_color(self):
        return "#FFFFFF" if self.theme == "dark" else "#000000"

    def _bind_variables(self):
        """Bind variable traces for external changes."""
        self.country_var.trace_add("write", self._on_country_var_change)
        self.city_var.trace_add("write", self._on_city_var_change)

    def _on_country_var_change(self, *args):
        """Handle external country variable change."""
        code = self.country_var.get()
        if code != self.current_country_code:
            self._on_country_selected(code)

    def _on_city_var_change(self, *args):
        """Handle external city variable change."""
        # City variable changed externally - update display
        pass

    def _on_country_selected(self, country_code: str):
        """Handle country selection."""
        self.current_country_code = country_code

        # Get cities for this country
        cities = self.cities_data.get(country_code, [])
        city_items = [{"name": city} for city in cities]

        # Update city combobox
        self.city_combo.set_items(city_items)
        self.city_combo.set_enabled(bool(cities))

        # Clear city selection
        self.city_var.set("")

        # Callback
        if self.on_country_change:
            self.on_country_change(country_code)

    def _init_values(self):
        """Initialize values after UI is fully constructed."""
        if self.country_var.get():
            self._on_country_selected(self.country_var.get())
        if self.city_var.get() and self.current_country_code:
            # City will be set after country loads cities
            pass

    def _on_city_selected(self, city_name: str, item: Dict):
        """Handle city selection."""
        if self.on_city_change:
            self.on_city_change(city_name)

    def set_theme(self, theme: str):
        """Update theme for both comboboxes."""
        self.theme = theme
        self.configure(background=self._get_bg_color())
        if self.country_combo:
            self.country_combo.set_theme(theme)
        if self.city_combo:
            self.city_combo.set_theme(theme)
        # Update labels
        for child in self.winfo_children():
            if isinstance(child, tk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Label) and subchild.cget("text") in ("الدولة:", "المدينة:"):
                        subchild.configure(
                            background=self._get_bg_color(),
                            foreground=self._get_text_color()
                        )