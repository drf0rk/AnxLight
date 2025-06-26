# ~ download-result.py | by ANXETY ~

from widget_factory import WidgetFactory    # WIDGETS
import json_utils as js                     # JSON

import ipywidgets as widgets
from pathlib import Path
import json
import time
import re
import os


osENV = os.environ

# Constants (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}   # k -> key; v -> value

HOME = PATHS['home_path']
SCR_PATH = PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']

UI = js.read(SETTINGS_PATH, 'WEBUI.current')

CSS = SCR_PATH / 'CSS'
widgets_css = CSS / 'download-result.css'


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


# ========================= WIDGETS ========================

HR = widgets.HTML('<hr class="divider-line">')
HEADER_DL = 'DOWNLOAD RESULTS'
VERSION = 'v0.58'

factory = WidgetFactory()

# Load CSS
factory.load_css(widgets_css)

# Define extensions to filter out
EXCLUDED_EXTENSIONS = {'.txt', '.yaml', '.log', '.json'}

## Functions
def output_container_generator(header, items, is_grid=False):
    """Create a container widget for output items."""
    header_widget = factory.create_html(f'<div class="section-title">{header} ➤</div>')
    content_widgets = [factory.create_html(f'<div class="output-item">{item}</div>') for item in items]

    container_method = factory.create_hbox if is_grid else factory.create_vbox    # hbox -> grid
    content_container = container_method(content_widgets).add_class('_horizontal' if is_grid else '')

    return factory.create_vbox([header_widget, content_container]).add_class('output-section')

def get_all_files_list(directory, extensions, excluded_dirs=[]):
    """Get all files in the directory and its subdirectories, excluding specified directories."""
    if not os.path.isdir(directory):
        return []

    files_list = []
    for root, dirs, files in os.walk(directory, followlinks=True):
        # Exclude specified directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs]

        for file in files:
            if file.endswith(extensions) and not file.endswith(tuple(EXCLUDED_EXTENSIONS)):
                files_list.append(file)  # Store only the file name
    return files_list

def get_folders_list(directory):
    """List folders in a directory, excluding hidden folders."""
    if not os.path.isdir(directory):
        return []
    return [
        folder for folder in os.listdir(directory)
        if os.path.isdir(os.path.join(directory, folder)) and not folder.startswith('__')
    ]

def get_controlnets_list(directory, filter_pattern):
    """List ControlNet files matching a specific pattern."""
    if not os.path.isdir(directory):
        return []
    filter_name = re.compile(filter_pattern)
    return [
        filter_name.match(file).group(1) if filter_name.match(file) else file
        for file in os.listdir(directory)
        if not file.endswith(tuple(EXCLUDED_EXTENSIONS)) and '.' in file
    ]

## Widgets
header_widget = factory.create_html(f'''
<div><span class="header-main-title">{HEADER_DL}</span> <span style="color: grey; opacity: 0.25;">| {VERSION}</span></div>
''')

# Models
models_list = get_all_files_list(model_dir, ('.safetensors', '.ckpt'))
models_widget = output_container_generator('Models', models_list)
# Vaes
vaes_list = get_all_files_list(vae_dir, ('.safetensors',))
vaes_widget = output_container_generator('VAEs', vaes_list)
# Embeddings
embed_filter = ['SD', 'XL']
embeddings_list = get_all_files_list(embed_dir, ('.safetensors', '.pt'), embed_filter)
embeddings_widget = output_container_generator('Embeddings', embeddings_list)
# LoRAs
loras_list = get_all_files_list(lora_dir, ('.safetensors',))
loras_widget = output_container_generator('LoRAs', loras_list)
# Extensions
extensions_list = get_folders_list(extension_dir)
extension_type = 'Nodes' if UI == 'ComfyUI' else 'Extensions'
extensions_widget = output_container_generator(extension_type, extensions_list, is_grid=True)
# ADetailers
adetailers_list = get_all_files_list(adetailer_dir, ('.safetensors', '.pt'))
adetailers_widget = output_container_generator('ADetailers', adetailers_list)
# Clips
clips_list = get_all_files_list(clip_dir, ('.safetensors',))
clips_widget = output_container_generator('Clips', clips_list)
# Unets
unets_list = get_all_files_list(unet_dir, ('.safetensors',))
unets_widget = output_container_generator('Unets', unets_list)
# (Clip) Visions
visions_list = get_all_files_list(vision_dir, ('.safetensors',))
visions_widget = output_container_generator('Visions', visions_list)
# (Text) Encoders
encoders_list = get_all_files_list(encoder_dir, ('.safetensors',))
encoders_widget = output_container_generator('Encoders', encoders_list)
# Diffusions (Models)
diffusions_list = get_all_files_list(diffusion_dir, ('.safetensors',))
diffusions_widget = output_container_generator('Diffusions', diffusions_list)
# ControlNet
controlnets_list = get_controlnets_list(control_dir, r'^[^_]*_[^_]*_[^_]*_(.*)_fp16\.safetensors')
controlnets_widget = output_container_generator('ControlNets', controlnets_list)

## Sorting and Output
widgets_dict = {
    models_widget: models_list,
    vaes_widget: vaes_list,
    embeddings_widget: embeddings_list,
    loras_widget: loras_list,
    extensions_widget: extensions_list,
    adetailers_widget: adetailers_list,
    clips_widget: clips_list,
    unets_widget: unets_list,
    visions_widget: visions_list,
    encoders_widget: encoders_list,
    diffusions_widget: diffusions_list,
    controlnets_widget: controlnets_list
}

outputs_widgets_list = [widget for widget, widget_list in widgets_dict.items() if widget_list]
result_output_widget = factory.create_hbox(outputs_widgets_list).add_class('result-output-container')

container_widget = factory.create_vbox([header_widget, HR, result_output_widget, HR],
                                       layout={'width': '1080px'}).add_class('result-container')
factory.display(container_widget)