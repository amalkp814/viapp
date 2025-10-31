
# Standard library imports
import os  # For environment variables and file paths

# Third-party library imports
import numpy as np  # For numerical operations and arrays
from faster_whisper import WhisperModel  # Local Whisper model

# Local module import
from utils import ConfigManager  # For configuration management


def create_local_model():
    """
    Create a local model using the faster-whisper library.
    Loads model based on config, chooses device and compute type.
    """
    ConfigManager.console_print('Creating local model...')
    local_model_options = ConfigManager.get_config_section('model_options')['local']
    compute_type = local_model_options['compute_type']
    model_path = local_model_options.get('model_path')

    # If using int8 quantization, force CPU usage
    if compute_type == 'int8':
        device = 'cpu'
        ConfigManager.console_print('Using int8 quantization, forcing CPU usage.')
    else:
        device = local_model_options['device']

    try:
        if model_path:
            ConfigManager.console_print(f'Loading model from: {model_path}')
            model = WhisperModel(model_path,
                                 device=device,
                                 compute_type=compute_type,
                                 download_root=None)  # Prevent automatic download
        else:
            model = WhisperModel(local_model_options['model'],
                                 device=device,
                                 compute_type=compute_type)
    except Exception as e:
        # If model fails to load, fall back to CPU
        ConfigManager.console_print(f'Error initializing WhisperModel: {e}')
        ConfigManager.console_print('Falling back to CPU.')
        model = WhisperModel(model_path or local_model_options['model'],
                             device='cpu',
                             compute_type=compute_type,
                             download_root=None if model_path else None)

    ConfigManager.console_print('Local model created.')
    return model


def transcribe_local(audio_data, local_model=None):
    """
    Transcribe an audio file using a local model.
    Converts audio to float32, runs transcription, and returns text.
    """
    if not local_model:
        local_model = create_local_model()
    model_options = ConfigManager.get_config_section('model_options')

    # Convert int16 audio to float32 for Whisper
    audio_data_float = audio_data.astype(np.float32) / 32768.0

    # Run transcription with options from config
    response = local_model.transcribe(audio=audio_data_float,
                                      language=model_options['common']['language'],
                                      initial_prompt=model_options['common']['initial_prompt'],
                                      condition_on_previous_text=model_options['local']['condition_on_previous_text'],
                                      temperature=model_options['common']['temperature'],
                                      vad_filter=model_options['local']['vad_filter'],)
    # Combine all segments into a single string
    return ''.join([segment.text for segment in list(response[0])])


def post_process_transcription(transcription):
    """
    Apply post-processing to the transcription.
    Modifies the text based on config (remove period, add space, lowercase).
    """
    transcription = transcription.strip()
    post_processing = ConfigManager.get_config_section('post_processing')
    if post_processing['remove_trailing_period'] and transcription.endswith('.'):
        transcription = transcription[:-1]
    if post_processing['add_trailing_space']:
        transcription += ' '
    if post_processing['remove_capitalization']:
        transcription = transcription.lower()

    return transcription


def transcribe(audio_data, local_model=None):
    """
    Transcribe audio data using a local model.
    This is the main entry point for transcription in the app.
    """
    if audio_data is None:
        return ''

    transcription = transcribe_local(audio_data, local_model)

    # Apply post-processing before returning
    return post_process_transcription(transcription)

