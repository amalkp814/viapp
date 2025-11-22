import io
import os
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

from utils import ConfigManager


def create_local_model():
    """
    Create and initialize a local Whisper model using the faster-whisper library.
    
    Reads configuration for model size, device (CPU/GPU), and compute type.
    Handles fallback to CPU if GPU initialization fails.
    
    Returns:
        WhisperModel: The initialized Whisper model.
    """
    ConfigManager.console_print("Creating local model...")
    local_model_options = ConfigManager.get_config_section("model_options")["local"]
    compute_type = local_model_options["compute_type"]
    model_path = local_model_options.get("model_path")

    if compute_type == "int8":
        device = "cpu"
        ConfigManager.console_print("Using int8 quantization, forcing CPU usage.")
    else:
        device = local_model_options["device"]

    try:
        if model_path:
            ConfigManager.console_print(f"Loading model from: {model_path}")
            model = WhisperModel(
                model_path, device=device, compute_type=compute_type, download_root=None
            )  # Prevent automatic download
        else:
            model = WhisperModel(
                local_model_options["model"], device=device, compute_type=compute_type
            )
    except Exception as e:
        ConfigManager.console_print(f"Error initializing WhisperModel: {e}")
        ConfigManager.console_print("Falling back to CPU.")
        model = WhisperModel(
            model_path or local_model_options["model"],
            device="cpu",
            compute_type=compute_type,
            download_root=None if model_path else None,
        )

    ConfigManager.console_print("Local model created.")
    return model


def transcribe_local(audio_data, local_model=None):
    """
    Transcribe audio data using the local Whisper model.
    
    Args:
        audio_data (np.array): The audio data to transcribe (int16).
        local_model (WhisperModel, optional): The model instance to use. If None, a new one is created.
        
    Returns:
        str: The transcribed text.
    """
    if not local_model:
        local_model = create_local_model()
    model_options = ConfigManager.get_config_section("model_options")

    # Convert int16 to float32 and normalize to [-1, 1]
    audio_data_float = audio_data.astype(np.float32) / 32768.0

    response = local_model.transcribe(
        audio=audio_data_float,
        language=model_options["common"]["language"],
        initial_prompt=model_options["common"]["initial_prompt"],
        condition_on_previous_text=model_options["local"]["condition_on_previous_text"],
        temperature=model_options["common"]["temperature"],
        vad_filter=model_options["local"]["vad_filter"],
    )
    return "".join([segment.text for segment in list(response[0])])


def post_process_transcription(transcription):
    """
    Apply post-processing rules to the transcribed text.
    
    Rules include:
    - Removing trailing periods
    - Adding trailing spaces
    - Removing capitalization
    
    Args:
        transcription (str): The raw transcribed text.
        
    Returns:
        str: The processed text.
    """
    transcription = transcription.strip()
    post_processing = ConfigManager.get_config_section("post_processing")
    if post_processing["remove_trailing_period"] and transcription.endswith("."):
        transcription = transcription[:-1]
    if post_processing["add_trailing_space"]:
        transcription += " "
    if post_processing["remove_capitalization"]:
        transcription = transcription.lower()

    return transcription


def transcribe(audio_data, local_model=None):
    """
    Main entry point for transcription.
    Orchestrates the transcription and post-processing steps.
    
    Args:
        audio_data (np.array): The audio data to transcribe.
        local_model (WhisperModel, optional): The model instance to use.
        
    Returns:
        str: The final processed transcription.
    """
    if audio_data is None:
        return ""

    transcription = transcribe_local(audio_data, local_model)

    return post_process_transcription(transcription)
