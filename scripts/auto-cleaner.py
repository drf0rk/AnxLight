# ~ auto-cleaner.py | by ANXETY ~

from widget_factory import WidgetFactory    # WIDGETS
import json_utils as js                     # JSON

from IPython.display import display, HTML, clear_output
import ipywidgets as widgets
from pathlib import Path
import psutil
import json
import time
import os


osENV = os.environ

# Constants (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}   # k -> key; v -> value

HOME = PATHS['home_path']
SCR_PATH = PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']

CSS = SCR_PATH / 'CSS'
cleaner_css = CSS / 'auto-cleaner.css'


# =================== loading settings V5 ==================

def load_settings(path):
    """Load settings from a JSON file."""
    try:
        return {
            **js.read(path, 'ENVIRONMENT'),
            **js.read(path, 'WIDGETS'),
            **js.read(path, 'WEBUI')
        }
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading settings: {e}")
        return {}

# Load settings
settings = load_settings(SETTINGS_PATH)
locals().update(settings)


# ================== AutoCleaner function ==================

def _update_memory_info():
    disk_space = psutil.disk_usage(os.getcwd())
    total = disk_space.total / (1024 ** 3)
    used = disk_space.used / (1024 ** 3)
    free = disk_space.free / (1024 ** 3)

    storage_info.value = f'''
    <div class="storage_info">Total storage: {total:.2f} GB <span style="color: #555">|</span> Used: {used:.2f} GB <span style="color: #555">|</span> Free: {free:.2f} GB</div>
    '''

def clean_directory(directory, directory_type):
    trash_extensions = {'.txt', '.aria2', '.ipynb_checkpoints'}
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif'}
    deleted_files = 0

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)

            if directory_type == 'Models' and file.endswith(tuple(image_extensions)):
                os.remove(file_path)
                continue

            if not file.endswith(tuple(trash_extensions)) and '.' in file:
                deleted_files += 1

            os.remove(file_path)

    return deleted_files

def generate_messages(deleted_files_dict):
    messages = []

    for key, value in deleted_files_dict.items():
        object_word = key
        messages.append(f"Deleted {value} {object_word}")
    return messages

def execute_button_press(button):
    selected_cleaners = auto_cleaner_widget.value
    deleted_files_dict = {}

    for option in selected_cleaners:
        if option in directories:
            deleted_files_dict[option] = clean_directory(directories[option], option)

    output.clear_output()

    with output:
        for message in generate_messages(deleted_files_dict):
            message_widget = HTML(f'<p class="output_message animated_message">{message}</p>')
            display(message_widget)

    _update_memory_info()

def hide_button_press(button):
    factory.close(container, class_names=['hide'], delay=0.5)


# =================== AutoCleaner Widgets ==================

# Initialize the WidgetFactory
factory = WidgetFactory()
HR = widgets.HTML('<hr>')

# Load Css
factory.load_css(cleaner_css)

directories = {
    'Images': output_dir,
    'Models': model_dir,
    'Vae': vae_dir,
    'LoRa': lora_dir,
    'ControlNet Models': control_dir
}

# --- storage memory ---
disk_space = psutil.disk_usage(os.getcwd())
total = disk_space.total / (1024 ** 3)
used = disk_space.used / (1024 ** 3)
free = disk_space.free / (1024 ** 3)

# UI Code
clean_options = list(directories.keys())

instruction_label = factory.create_html('''
<span class="instruction">Use <span style="color: #B2B2B2;">ctrl</span> or <span style="color: #B2B2B2;">shift</span> for multiple selections.</span>
''')
auto_cleaner_widget = factory.create_select_multiple(clean_options, '', [], layout={'width': 'auto'}, class_names=['custom_select_multiple'])
output = widgets.Output().add_class('output_panel')
# ---
execute_button = factory.create_button('Execute Cleaning', class_names=['button_execute', 'cleaner_button'])
hide_button = factory.create_button('Hide Widget', class_names=['button_hide', 'cleaner_button'])

# Button Click
execute_button.on_click(execute_button_press)
hide_button.on_click(hide_button_press)
# ---
storage_info = factory.create_html(f'''
<div class="storage_info">Total storage: {total:.2f} GB <span style="color: #555">|</span> Used: {used:.2f} GB <span style="color: #555">|</span> Free: {free:.2f} GB</div>
''')
# ---
buttons = factory.create_hbox([execute_button, hide_button])
lower_information_panel = factory.create_hbox([buttons, storage_info], class_names=['lower_information_panel'])

# Create a horizontal layout for the selection and output areas
hbox_layout = factory.create_hbox([auto_cleaner_widget, output], class_names=['selection_output_layout'])

container = factory.create_vbox([instruction_label, HR, hbox_layout, HR, lower_information_panel],
                                layout={'width': '1080px'}, class_names=['cleaner_container'])

factory.display(container)