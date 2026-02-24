#!/usr/bin/env python3
"""
A Kivy GUI application for continuously monitoring log files like 'tail -f'.
Fixed version with correct indentation and working features.
"""

import os
import time
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard


class CopyableTextInput(TextInput):
    """TextInput with right-click context menu for copying"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.context_menu = None

    def on_touch_down(self, touch):
        if getattr(touch, 'button', None) == 'right' and self.collide_point(*touch.pos):
            self.show_context_menu(touch)
            return True
        return super().on_touch_down(touch)

    def show_context_menu(self, touch):
        """Show context menu on right-click"""
        if self.context_menu:
            self.context_menu.dismiss()

        menu_layout = BoxLayout(orientation='vertical', spacing=5, padding=5)

        copy_btn = Button(
            text='Copy Selected',
            size_hint_y=None,
            height=40,
            background_color=(0.2, 0.6, 0.8, 1),
        )
        copy_btn.bind(on_press=lambda *_: self.copy_selected())

        copy_all_btn = Button(
            text='Copy All',
            size_hint_y=None,
            height=40,
            background_color=(0.3, 0.7, 0.5, 1),
        )
        copy_all_btn.bind(on_press=lambda *_: self.copy_all())

        menu_layout.add_widget(copy_btn)
        menu_layout.add_widget(copy_all_btn)

        self.context_menu = Popup(
            title='Copy Options',
            content=menu_layout,
            size_hint=(None, None),
            size=(200, 120),
            auto_dismiss=True,
        )

        # Open first, then position to avoid pos_hint issues
        self.context_menu.open()

        # Position menu near the click, ensuring it stays on screen
        menu_x = min(touch.x, Window.width - 200)
        menu_y = max(touch.y - 120, 0)
        self.context_menu.pos = (menu_x, menu_y)

    def copy_selected(self):
        """Copy selected text to clipboard"""
        if self.selection_text:
            Clipboard.copy(self.selection_text)
            print(f"Copied {len(self.selection_text)} characters to clipboard")
        else:
            print("No text selected")

        if self.context_menu:
            self.context_menu.dismiss()

    def copy_all(self):
        """Copy all text to clipboard"""
        if self.text:
            Clipboard.copy(self.text)
            print(f"Copied all {len(self.text)} characters to clipboard")
        else:
            print("No text to copy")

        if self.context_menu:
            self.context_menu.dismiss()


class LogTailApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_path = None
        self.follow_thread = None
        self.stop_following = False
        self.file_handle = None
        self.search_text = ''
        self.search_matches = []
        self.current_match_index = 0
        self.case_sensitive = False
        self.all_log_text = ''

    def build(self):
        Window.size = (900, 700)
        Window.clearcolor = (1, 1, 1, 1)
        self.title = "Log Tail Viewer"

        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # File path input section
        path_section = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)

        path_label = Label(text='File Path:', size_hint_x=0.12, halign='left', valign='middle', color=(0, 0, 0, 1))
        path_label.bind(size=path_label.setter('text_size'))

        self.path_input = TextInput(text='', multiline=False, size_hint_x=0.6, hint_text='Enter file path...')

        load_btn = Button(text='Load', size_hint_x=0.14, background_color=(0.3, 0.7, 0.3, 1))
        load_btn.bind(on_press=self.load_from_input)

        browse_btn = Button(text='Browse', size_hint_x=0.14, background_color=(0.2, 0.6, 0.8, 1))
        browse_btn.bind(on_press=self.open_file_browser)

        path_section.add_widget(path_label)
        path_section.add_widget(self.path_input)
        path_section.add_widget(load_btn)
        path_section.add_widget(browse_btn)

        # Status section
        status_section = BoxLayout(orientation='horizontal', size_hint_y=None, height=30, spacing=10)
        self.file_label = Label(text='No file loaded', size_hint_x=0.8, halign='left', valign='middle', color=(0, 0, 0, 1))
        self.file_label.bind(size=self.file_label.setter('text_size'))

        clear_btn = Button(text='Stop & Clear', size_hint_x=0.2, background_color=(0.8, 0.3, 0.3, 1))
        clear_btn.bind(on_press=self.stop_and_clear)

        status_section.add_widget(self.file_label)
        status_section.add_widget(clear_btn)

        # Follow section
        follow_section = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        follow_label = Label(text='Follow log (tail -f):', size_hint_x=0.3, halign='left', valign='middle', color=(0, 0, 0, 1))
        follow_label.bind(size=follow_label.setter('text_size'))

        self.follow_checkbox = CheckBox(active=False, size_hint_x=0.1, background_checkbox_normal='atlas://data/images/defaulttheme/checkbox_off', background_checkbox_down='atlas://data/images/defaulttheme/checkbox_on')
        self.follow_checkbox.bind(active=self.toggle_follow)
        # Make checkbox more visible with bright cyan color
        self.follow_checkbox.background_color = (0, 1, 1, 1)

        self.status_label = Label(text='Ready', size_hint_x=0.6, halign='left', valign='middle', color=(0, 0, 0, 1))
        self.status_label.bind(size=self.status_label.setter('text_size'))

        follow_section.add_widget(follow_label)
        follow_section.add_widget(self.follow_checkbox)
        follow_section.add_widget(self.status_label)

        # Search section
        search_section = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        
        search_label = Label(text='Search:', size_hint_x=0.12, halign='left', valign='middle', color=(0, 0, 0, 1))
        search_label.bind(size=search_label.setter('text_size'))
        
        self.search_input = TextInput(text='', multiline=False, size_hint_x=0.35, hint_text='Enter search text...', background_color=(1, 1, 1, 1), foreground_color=(0, 0, 0, 1))
        
        find_next_btn = Button(text='Find Next', size_hint_x=0.15, background_color=(0.2, 0.7, 0.8, 1))
        find_next_btn.bind(on_press=self.find_next)
        
        show_all_btn = Button(text='Show Matches', size_hint_x=0.15, background_color=(0.7, 0.5, 0.2, 1))
        show_all_btn.bind(on_press=self.show_all_matches)
        
        case_label = Label(text='Case Sensitive:', size_hint_x=0.12, halign='left', valign='middle', color=(0, 0, 0, 1))
        case_label.bind(size=case_label.setter('text_size'))
        
        self.case_sensitive_checkbox = CheckBox(active=False, size_hint_x=0.08)
        self.case_sensitive_checkbox.bind(active=self.on_case_sensitive_toggle)
        # Make checkbox more visible with bright magenta color
        self.case_sensitive_checkbox.background_color = (1, 0, 1, 1)
        
        clear_search_btn = Button(text='Clear', size_hint_x=0.08, background_color=(0.6, 0.6, 0.6, 1))
        clear_search_btn.bind(on_press=self.clear_search)
        
        search_section.add_widget(search_label)
        search_section.add_widget(self.search_input)
        search_section.add_widget(find_next_btn)
        search_section.add_widget(show_all_btn)
        search_section.add_widget(case_label)
        search_section.add_widget(self.case_sensitive_checkbox)
        search_section.add_widget(clear_search_btn)

        # Log display section
        scroll_view = ScrollView(size_hint=(1, 1))
        self.log_display = CopyableTextInput(text='', readonly=True, multiline=True, font_size=12, background_color=(1, 1, 1, 1), foreground_color=(0, 0, 0, 1))
        scroll_view.add_widget(self.log_display)

        main_layout.add_widget(path_section)
        main_layout.add_widget(status_section)
        main_layout.add_widget(follow_section)
        main_layout.add_widget(search_section)
        main_layout.add_widget(scroll_view)

        return main_layout

    def load_from_input(self, instance):
        file_path = self.path_input.text.strip()
        if not file_path:
            self.status_label.text = 'Please enter a file path'
            return
        if not os.path.exists(file_path):
            self.status_label.text = f'Error: Path not found - {file_path}'
            return
        if os.path.isdir(file_path):
            self.open_file_browser_at_path(file_path)
            return
        self.load_file(file_path)

    def open_file_browser(self, instance):
        start_path = self.path_input.text.strip() or os.path.expanduser('~')
        self.open_file_browser_at_path(start_path)

    def open_file_browser_at_path(self, start_path):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        file_chooser = FileChooserListView(path=start_path, filters=['*.log', '*.txt', '*'])

        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        select_btn = Button(text='Select', background_color=(0.2, 0.6, 0.8, 1))
        cancel_btn = Button(text='Cancel', background_color=(0.6, 0.6, 0.6, 1))

        button_layout.add_widget(cancel_btn)
        button_layout.add_widget(select_btn)

        content.add_widget(file_chooser)
        content.add_widget(button_layout)

        popup = Popup(title='Select Log File', content=content, size_hint=(0.9, 0.9))

        def on_select(_):
            selection = file_chooser.selection
            if selection:
                popup.dismiss()
                self.load_file(selection[0])

        cancel_btn.bind(on_press=lambda *_: popup.dismiss())
        select_btn.bind(on_press=on_select)
        popup.open()

    def load_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except Exception as e:
            self.status_label.text = f'Error opening file: {e}'
            return
        self.file_path = path
        self.file_label.text = os.path.basename(path)
        self.log_display.text = text
        self.all_log_text = ''  # Reset so we don't restore old filtered content
        self.search_input.text = ''  # Clear search on new file
        self.status_label.text = f'Loaded {path}'

        if self.follow_checkbox.active:
            self.start_following()

    def start_following(self):
        if not self.file_path:
            self.status_label.text = 'No file to follow'
            return
        if self.follow_thread and self.follow_thread.is_alive():
            return
        self.stop_following = False
        self.follow_thread = threading.Thread(target=self._follow_file, daemon=True)
        self.follow_thread.start()
        self.status_label.text = 'Following'

    def _follow_file(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Go to end
                f.seek(0, os.SEEK_END)
                while not self.stop_following:
                    line = f.readline()
                    if not line:
                        time.sleep(0.2)
                        continue
                    Clock.schedule_once(lambda dt, l=line: self.append_text(l))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f'Follow error: {e}'))

    def append_text(self, text):
        self.log_display.text += text
        self.log_display.cursor = (len(self.log_display.text), 0)

    def stop_and_clear(self, instance):
        self.stop_following = True
        self.file_path = None
        self.file_label.text = 'No file loaded'
        self.log_display.text = ''
        self.status_label.text = 'Cleared'

    def toggle_follow(self, checkbox, value):
        if value:
            self.start_following()
        else:
            self.stop_following = True


    def find_next(self, instance):
        """Find and navigate to next matching text"""
        search_term = self.search_input.text
        if not search_term:
            self.status_label.text = 'Enter search text'
            return
        
        self.search_text = search_term
        text_to_search = self.log_display.text
        
        if not self.case_sensitive:
            text_to_search = text_to_search.lower()
            search_term = search_term.lower()
        
        # Find all matches
        self.search_matches = []
        start = 0
        while True:
            pos = text_to_search.find(search_term, start)
            if pos == -1:
                break
            self.search_matches.append(pos)
            start = pos + 1
        
        if not self.search_matches:
            self.status_label.text = f'No matches found for "{search_term}"'
            return
        
        # Navigate to next match
        if self.current_match_index >= len(self.search_matches):
            self.current_match_index = 0
        
        match_pos = self.search_matches[self.current_match_index]
        self.log_display.cursor = (match_pos, 0)
        
        self.status_label.text = f'Match {self.current_match_index + 1} of {len(self.search_matches)}'
        self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)

    def show_all_matches(self, instance):
        """Display only lines containing the search term"""
        search_term = self.search_input.text
        if not search_term:
            self.status_label.text = 'Enter search text'
            return
        
        self.all_log_text = self.log_display.text
        lines = self.all_log_text.split('\n')
        matching_lines = []
        
        for line in lines:
            if self.case_sensitive:
                if search_term in line:
                    matching_lines.append(line)
            else:
                if search_term.lower() in line.lower():
                    matching_lines.append(line)
        
        if not matching_lines:
            self.status_label.text = f'No matching lines found'
            return
        
        self.log_display.text = '\n'.join(matching_lines)
        self.status_label.text = f'Showing {len(matching_lines)} matching lines'

    def clear_search(self, instance):
        """Clear search and restore original log"""
        self.search_input.text = ''
        self.search_matches = []
        self.current_match_index = 0
        
        # Restore original log if it was filtered
        if self.all_log_text:
            self.log_display.text = self.all_log_text
            self.all_log_text = ''
        
        self.status_label.text = 'Search cleared'

    def on_case_sensitive_toggle(self, checkbox, value):
        """Handle case sensitive checkbox toggle"""
        self.case_sensitive = value
        if self.search_input.text:
            self.current_match_index = 0
            self.status_label.text = 'Case sensitive: ' + ('ON' if value else 'OFF')


if __name__ == '__main__':
    LogTailApp().run()
