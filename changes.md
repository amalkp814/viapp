# Viapp Code Changes

## Change 1: VAD Logic Optimization (Silence Buffering)

> **Note:** This document outlines a critical improvement to the Voice Activity Detection (VAD) logic in `src/result_thread.py`.

### 1. Problem Analysis: The "Silence Stripping" Issue

#### Current Behavior

In the current implementation of `_process_audio_queue`, when the VAD detects speech, it sets a `speech_detected` flag and starts recording. However, when it detects a frame of silence *while* this flag is active (i.e., a pause between words), it increments a silence counter but **does not append the silent frame to the recording buffer**.

#### The Impact

This effectively "strips" all silence from the audio sent to the Whisper model.

- **Input**: "Hello [pause] World"
- **Audio Sent to Model**: "HelloWorld" (concatenated abruptly)

This unnatural concatenation destroys the prosody (rhythm) of speech. It can cause the Whisper model to:

1. Merge words together incorrectly.
2. Fail to recognize sentence boundaries.
3. Hallucinate text due to the unnatural speed of the audio.

### 2. Proposed Solution: Silence Buffering

To fix this, we must treat silence that occurs *during* an active speech segment as part of the speech. We should append these silent frames to the buffer until the silence threshold (e.g., 900ms) is reached, at which point we consider the sentence finished.

#### Key Changes

1. **Buffer Silence**: When `speech_detected` is True but `is_speech` is False, we must append the current frame to the `recording` list.
2. **Trim (Optional)**: Optionally, we can trim the *trailing* silence (the 900ms used to detect the end) before sending it to the model, but keeping it is usually harmless for Whisper.

### 3. Optimized Process Flow Diagram

The following diagram illustrates the **corrected** logic. The key difference is the arrow from `Silence > Threshold? -- No` pointing to `Buffer Chunk`, ensuring natural pauses are preserved.

```mermaid
flowchart TD
    Start([Start Thread]) --> InitStream[Open Audio Stream]
    InitStream --> CheckRun{Is Running?}
    
    subgraph AudioLoop [Processing Loop]
        CheckRun -- Yes --> Read[Read 30ms Chunk]
        Read --> VAD{Is Speech?}
        
        %% Speech Detected Path
        VAD -- Yes --> SpeechTrue[Set SpeechDetected = True]
        SpeechTrue --> ResetSil[Reset Silence Counter]
        ResetSil --> Buffer[Append Chunk to Buffer]
        
        %% Silence Path
        VAD -- No --> CheckActive{Was Speech Active?}
        CheckActive -- No --> CheckRun
        
        CheckActive -- Yes --> IncSil[Increment Silence Counter]
        IncSil --> CheckThresh{Silence > Threshold?}
        
        %% CRITICAL CHANGE HERE:
        %% We now buffer the silence if we haven't reached the threshold yet.
        CheckThresh -- No --> Buffer
        
        CheckThresh -- Yes --> Finalize[Finalize Chunk]
    end
    
    Finalize --> Yield[Yield Audio Data]
    Yield --> Transcribe[Transcribe & Output]
    Transcribe --> Clear[Clear Buffer]
    Clear --> ResetFlag[Set SpeechDetected = False]
    ResetFlag --> CheckRun
    
    CheckRun -- No --> Stop([Stop Thread])
```

### 4. Implementation Details

#### Target File: `src/result_thread.py`

We need to modify the `_process_audio_queue` method.

##### Current Code (Lines 232-233)

```python
                elif speech_detected:
                    silent_frame_count += 1
                    # Silent frame is IGNORED here
```

##### Proposed Code

```python
                elif speech_detected:
                    silent_frame_count += 1
                    recording.extend(frame)  # <--- CRITICAL FIX: Keep the silence
```

### 5. Benefits of this Change

1. **Natural Sounding Audio**: The audio passed to Whisper will sound like a normal recording, pauses included.
2. **Improved Accuracy**: Whisper relies on context and pacing. Preserving silence helps it distinguish between "Let's eat, Grandma" and "Let's eat Grandma".
3. **Robustness**: Reduces the chance of words being cut off if the VAD flickers briefly during a soft consonant.

---

## Change 2: Dynamic Silence Threshold

> **Note:** This section outlines a proposed improvement to make the silence threshold dynamic based on the user's speaking pace.

### 1. Problem Analysis: Static Thresholds

#### Current Behavior

The application uses a fixed silence threshold (default 900ms) to determine when a sentence has ended.

#### The Impact

- **Fast Talkers**: May feel the app is too slow to finalize sentences, waiting nearly a second after they stop speaking.
- **Slow Talkers**: May have their sentences cut off prematurely if they pause to think.

### 2. Proposed Solution: Adaptive Threshold

Implement a simple adaptive mechanism that adjusts the silence threshold based on the length of the current speech segment.

#### Logic

- **Short Utterances**: Use a shorter threshold (e.g., 500ms) for quick commands (e.g., "Yes", "No", "Stop").
- **Long Utterances**: Use a longer threshold (e.g., 1000ms-1200ms) for dictation, allowing for natural pauses for thought.

#### Implementation Strategy

# Viapp Code Changes

## Change 1: VAD Logic Optimization (Silence Buffering)

> **Note:** This document outlines a critical improvement to the Voice Activity Detection (VAD) logic in `src/result_thread.py`.

### 1. Problem Analysis: The "Silence Stripping" Issue

#### Current Behavior

In the current implementation of `_process_audio_queue`, when the VAD detects speech, it sets a `speech_detected` flag and starts recording. However, when it detects a frame of silence *while* this flag is active (i.e., a pause between words), it increments a silence counter but **does not append the silent frame to the recording buffer**.

#### The Impact

This effectively "strips" all silence from the audio sent to the Whisper model.

- **Input**: "Hello [pause] World"
- **Audio Sent to Model**: "HelloWorld" (concatenated abruptly)

This unnatural concatenation destroys the prosody (rhythm) of speech. It can cause the Whisper model to:

1. Merge words together incorrectly.
2. Fail to recognize sentence boundaries.
3. Hallucinate text due to the unnatural speed of the audio.

### 2. Proposed Solution: Silence Buffering

To fix this, we must treat silence that occurs *during* an active speech segment as part of the speech. We should append these silent frames to the buffer until the silence threshold (e.g., 900ms) is reached, at which point we consider the sentence finished.

#### Key Changes

1. **Buffer Silence**: When `speech_detected` is True but `is_speech` is False, we must append the current frame to the `recording` list.
2. **Trim (Optional)**: Optionally, we can trim the *trailing* silence (the 900ms used to detect the end) before sending it to the model, but keeping it is usually harmless for Whisper.

### 3. Optimized Process Flow Diagram

The following diagram illustrates the **corrected** logic. The key difference is the arrow from `Silence > Threshold? -- No` pointing to `Buffer Chunk`, ensuring natural pauses are preserved.

```mermaid
flowchart TD
    Start([Start Thread]) --> InitStream[Open Audio Stream]
    InitStream --> CheckRun{Is Running?}
    
    subgraph AudioLoop [Processing Loop]
        CheckRun -- Yes --> Read[Read 30ms Chunk]
        Read --> VAD{Is Speech?}
        
        %% Speech Detected Path
        VAD -- Yes --> SpeechTrue[Set SpeechDetected = True]
        SpeechTrue --> ResetSil[Reset Silence Counter]
        ResetSil --> Buffer[Append Chunk to Buffer]
        
        %% Silence Path
        VAD -- No --> CheckActive{Was Speech Active?}
        CheckActive -- No --> CheckRun
        
        CheckActive -- Yes --> IncSil[Increment Silence Counter]
        IncSil --> CheckThresh{Silence > Threshold?}
        
        %% CRITICAL CHANGE HERE:
        %% We now buffer the silence if we haven't reached the threshold yet.
        CheckThresh -- No --> Buffer
        
        CheckThresh -- Yes --> Finalize[Finalize Chunk]
    end
    
    Finalize --> Yield[Yield Audio Data]
    Yield --> Transcribe[Transcribe & Output]
    Transcribe --> Clear[Clear Buffer]
    Clear --> ResetFlag[Set SpeechDetected = False]
    ResetFlag --> CheckRun
    
    CheckRun -- No --> Stop([Stop Thread])
```

### 4. Implementation Details

#### Target File: `src/result_thread.py`

We need to modify the `_process_audio_queue` method.

##### Current Code (Lines 232-233)

```python
                elif speech_detected:
                    silent_frame_count += 1
                    # Silent frame is IGNORED here
```

##### Proposed Code

```python
                elif speech_detected:
                    silent_frame_count += 1
                    recording.extend(frame)  # <--- CRITICAL FIX: Keep the silence
```

### 5. Benefits of this Change

1. **Natural Sounding Audio**: The audio passed to Whisper will sound like a normal recording, pauses included.
2. **Improved Accuracy**: Whisper relies on context and pacing. Preserving silence helps it distinguish between "Let's eat, Grandma" and "Let's eat Grandma".
3. **Robustness**: Reduces the chance of words being cut off if the VAD flickers briefly during a soft consonant.

---

## Change 2: Dynamic Silence Threshold

> **Note:** This section outlines a proposed improvement to make the silence threshold dynamic based on the user's speaking pace.

### 1. Problem Analysis: Static Thresholds

#### Current Behavior

The application uses a fixed silence threshold (default 900ms) to determine when a sentence has ended.

#### The Impact

- **Fast Talkers**: May feel the app is too slow to finalize sentences, waiting nearly a second after they stop speaking.
- **Slow Talkers**: May have their sentences cut off prematurely if they pause to think.

### 2. Proposed Solution: Adaptive Threshold

Implement a simple adaptive mechanism that adjusts the silence threshold based on the length of the current speech segment.

#### Logic

- **Short Utterances**: Use a shorter threshold (e.g., 500ms) for quick commands (e.g., "Yes", "No", "Stop").
- **Long Utterances**: Use a longer threshold (e.g., 1000ms-1200ms) for dictation, allowing for natural pauses for thought.

#### Implementation Strategy

1. Track the duration of the current `speech_detected` session.
2. If `duration < 2 seconds`: `silence_threshold = 500ms`
3. If `duration >= 2 seconds`: `silence_threshold = 1000ms`

### 3. Benefits

1. **Responsiveness**: Makes the app feel snappier for short commands.
2. **Forgiveness**: Prevents cutting off users during longer dictation sessions.

---

## Change 3: Input Buffer Flushing

> **Note:** This section addresses an issue where transcribed text is correctly generated but fails to appear fully in the target application until a subsequent key press.

### 1. Problem Analysis: Event Loop Blocking & Buffer Stalls

#### Symptoms

- The terminal shows the correct transcription: `Transcription completed... Post-processed line: "Hello World"`
- The target application (Notepad, Browser) shows: `"Hello Wor"` or nothing at all.
- Pressing any key (e.g., Space) suddenly causes the missing characters to appear.

#### Root Cause

This is a common issue with `pynput` and OS-level input simulation.

1. **Event Loop Blocking**: The `InputSimulator` might be running on the main thread or blocking the event loop, preventing the OS from processing the simulated events immediately.
2. **Missing Flush**: Some applications buffer input events and wait for a "commit" signal (like a space or enter) or a specific time interval.
3. **Race Conditions**: If the simulation happens too fast, the OS input queue might get overwhelmed or desynchronized.

### 2. Proposed Solution: Explicit Flush & Delays

We need to ensure that the input simulation is robust and forces the OS to process the events.

#### Strategy

1. **Add Small Delays**: Introduce a tiny delay between keystrokes (if not already present) to allow the OS to process each event.
2. **Explicit Flush**: Simulate a "dummy" non-printing key event (like `Shift` up/down) at the end of the typing sequence to force the OS to flush its input buffer.
3. **Process Events**: Ensure the Qt event loop processes events after typing.

### 3. Implementation Plan

#### Target File: `src/input_simulation.py`

Modify the `_PynputSimulator.typewrite` method.

#### Proposed Code Changes

```python
    def typewrite(self, text):
        text = self._perform_word_replacements(text)
        
        # 1. Type the text
        self.keyboard.type(text)
        
        # 2. Force Flush Strategy
        # Simulate a harmless key press to flush the OS buffer
        # This is often required for applications that buffer input (like some editors or remote desktops)
- **Short Utterances**: Use a shorter threshold (e.g., 500ms) for quick commands (e.g., "Yes", "No", "Stop").
- **Long Utterances**: Use a longer threshold (e.g., 1000ms-1200ms) for dictation, allowing for natural pauses for thought.

#### Implementation Strategy

# Viapp Code Changes

## Change 1: VAD Logic Optimization (Silence Buffering)

> **Note:** This document outlines a critical improvement to the Voice Activity Detection (VAD) logic in `src/result_thread.py`.

### 1. Problem Analysis: The "Silence Stripping" Issue

#### Current Behavior

In the current implementation of `_process_audio_queue`, when the VAD detects speech, it sets a `speech_detected` flag and starts recording. However, when it detects a frame of silence *while* this flag is active (i.e., a pause between words), it increments a silence counter but **does not append the silent frame to the recording buffer**.

#### The Impact

This effectively "strips" all silence from the audio sent to the Whisper model.

- **Input**: "Hello [pause] World"
- **Audio Sent to Model**: "HelloWorld" (concatenated abruptly)

This unnatural concatenation destroys the prosody (rhythm) of speech. It can cause the Whisper model to:

1. Merge words together incorrectly.
2. Fail to recognize sentence boundaries.
3. Hallucinate text due to the unnatural speed of the audio.

### 2. Proposed Solution: Silence Buffering

To fix this, we must treat silence that occurs *during* an active speech segment as part of the speech. We should append these silent frames to the buffer until the silence threshold (e.g., 900ms) is reached, at which point we consider the sentence finished.

#### Key Changes

1. **Buffer Silence**: When `speech_detected` is True but `is_speech` is False, we must append the current frame to the `recording` list.
2. **Trim (Optional)**: Optionally, we can trim the *trailing* silence (the 900ms used to detect the end) before sending it to the model, but keeping it is usually harmless for Whisper.

### 3. Optimized Process Flow Diagram

The following diagram illustrates the **corrected** logic. The key difference is the arrow from `Silence > Threshold? -- No` pointing to `Buffer Chunk`, ensuring natural pauses are preserved.

```mermaid
flowchart TD
    Start([Start Thread]) --> InitStream[Open Audio Stream]
    InitStream --> CheckRun{Is Running?}
    
    subgraph AudioLoop [Processing Loop]
        CheckRun -- Yes --> Read[Read 30ms Chunk]
        Read --> VAD{Is Speech?}
        
        %% Speech Detected Path
        VAD -- Yes --> SpeechTrue[Set SpeechDetected = True]
        SpeechTrue --> ResetSil[Reset Silence Counter]
        ResetSil --> Buffer[Append Chunk to Buffer]
        
        %% Silence Path
        VAD -- No --> CheckActive{Was Speech Active?}
        CheckActive -- No --> CheckRun
        
        CheckActive -- Yes --> IncSil[Increment Silence Counter]
        IncSil --> CheckThresh{Silence > Threshold?}
        
        %% CRITICAL CHANGE HERE:
        %% We now buffer the silence if we haven't reached the threshold yet.
        CheckThresh -- No --> Buffer
        
        CheckThresh -- Yes --> Finalize[Finalize Chunk]
    end
    
    Finalize --> Yield[Yield Audio Data]
    Yield --> Transcribe[Transcribe & Output]
    Transcribe --> Clear[Clear Buffer]
    Clear --> ResetFlag[Set SpeechDetected = False]
    ResetFlag --> CheckRun
    
    CheckRun -- No --> Stop([Stop Thread])
```

### 4. Implementation Details

#### Target File: `src/result_thread.py`

We need to modify the `_process_audio_queue` method.

##### Current Code (Lines 232-233)

```python
                elif speech_detected:
                    silent_frame_count += 1
                    # Silent frame is IGNORED here
```

##### Proposed Code

```python
                elif speech_detected:
                    silent_frame_count += 1
                    recording.extend(frame)  # <--- CRITICAL FIX: Keep the silence
```

### 5. Benefits of this Change

1. **Natural Sounding Audio**: The audio passed to Whisper will sound like a normal recording, pauses included.
2. **Improved Accuracy**: Whisper relies on context and pacing. Preserving silence helps it distinguish between "Let's eat, Grandma" and "Let's eat Grandma".
3. **Robustness**: Reduces the chance of words being cut off if the VAD flickers briefly during a soft consonant.

---

## Change 2: Dynamic Silence Threshold

> **Note:** This section outlines a proposed improvement to make the silence threshold dynamic based on the user's speaking pace.

### 1. Problem Analysis: Static Thresholds

#### Current Behavior

The application uses a fixed silence threshold (default 900ms) to determine when a sentence has ended.

#### The Impact

- **Fast Talkers**: May feel the app is too slow to finalize sentences, waiting nearly a second after they stop speaking.
- **Slow Talkers**: May have their sentences cut off prematurely if they pause to think.

### 2. Proposed Solution: Adaptive Threshold

Implement a simple adaptive mechanism that adjusts the silence threshold based on the length of the current speech segment.

#### Logic

- **Short Utterances**: Use a shorter threshold (e.g., 500ms) for quick commands (e.g., "Yes", "No", "Stop").
- **Long Utterances**: Use a longer threshold (e.g., 1000ms-1200ms) for dictation, allowing for natural pauses for thought.

#### Implementation Strategy

1. Track the duration of the current `speech_detected` session.
2. If `duration < 2 seconds`: `silence_threshold = 500ms`
3. If `duration >= 2 seconds`: `silence_threshold = 1000ms`

### 3. Benefits

1. **Responsiveness**: Makes the app feel snappier for short commands.
2. **Forgiveness**: Prevents cutting off users during longer dictation sessions.

---

## Change 3: Input Buffer Flushing

> **Note:** This section addresses an issue where transcribed text is correctly generated but fails to appear fully in the target application until a subsequent key press.

### 1. Problem Analysis: Event Loop Blocking & Buffer Stalls

#### Symptoms

- The terminal shows the correct transcription: `Transcription completed... Post-processed line: "Hello World"`
- The target application (Notepad, Browser) shows: `"Hello Wor"` or nothing at all.
- Pressing any key (e.g., Space) suddenly causes the missing characters to appear.

#### Root Cause

This is a common issue with `pynput` and OS-level input simulation.

1. **Event Loop Blocking**: The `InputSimulator` might be running on the main thread or blocking the event loop, preventing the OS from processing the simulated events immediately.
2. **Missing Flush**: Some applications buffer input events and wait for a "commit" signal (like a space or enter) or a specific time interval.
3. **Race Conditions**: If the simulation happens too fast, the OS input queue might get overwhelmed or desynchronized.

### 2. Proposed Solution: Explicit Flush & Delays

We need to ensure that the input simulation is robust and forces the OS to process the events.

#### Strategy

1. **Add Small Delays**: Introduce a tiny delay between keystrokes (if not already present) to allow the OS to process each event.
2. **Explicit Flush**: Simulate a "dummy" non-printing key event (like `Shift` up/down) at the end of the typing sequence to force the OS to flush its input buffer.
3. **Process Events**: Ensure the Qt event loop processes events after typing.

### 3. Implementation Plan

#### Target File: `src/input_simulation.py`

Modify the `_PynputSimulator.typewrite` method.

#### Proposed Code Changes

```python
    def typewrite(self, text):
        text = self._perform_word_replacements(text)
        
        # 1. Type the text
        self.keyboard.type(text)
        
        # 2. Force Flush Strategy
        # Simulate a harmless key press to flush the OS buffer
        # This is often required for applications that buffer input (like some editors or remote desktops)
        time.sleep(0.01) 
        self.keyboard.touch(Key.shift, False) # Release shift just in case
        time.sleep(0.01)
```

### 4. Benefits

## Change 1: VAD Logic Optimization (Silence Buffering)

> **Note:** This document outlines a critical improvement to the Voice Activity Detection (VAD) logic in `src/result_thread.py`.

### 1. Problem Analysis: The "Silence Stripping" Issue

#### Current Behavior

In the current implementation of `_process_audio_queue`, when the VAD detects speech, it sets a `speech_detected` flag and starts recording. However, when it detects a frame of silence *while* this flag is active (i.e., a pause between words), it increments a silence counter but **does not append the silent frame to the recording buffer**.

#### The Impact

This effectively "strips" all silence from the audio sent to the Whisper model.

- **Input**: "Hello [pause] World"
- **Audio Sent to Model**: "HelloWorld" (concatenated abruptly)

This unnatural concatenation destroys the prosody (rhythm) of speech. It can cause the Whisper model to:

1. Merge words together incorrectly.
2. Fail to recognize sentence boundaries.
3. Hallucinate text due to the unnatural speed of the audio.

### 2. Proposed Solution: Silence Buffering

To fix this, we must treat silence that occurs *during* an active speech segment as part of the speech. We should append these silent frames to the buffer until the silence threshold (e.g., 900ms) is reached, at which point we consider the sentence finished.

#### Key Changes

1. **Buffer Silence**: When `speech_detected` is True but `is_speech` is False, we must append the current frame to the `recording` list.
2. **Trim (Optional)**: Optionally, we can trim the *trailing* silence (the 900ms used to detect the end) before sending it to the model, but keeping it is usually harmless for Whisper.

### 3. Optimized Process Flow Diagram

The following diagram illustrates the **corrected** logic. The key difference is the arrow from `Silence > Threshold? -- No` pointing to `Buffer Chunk`, ensuring natural pauses are preserved.

```mermaid
flowchart TD
    Start([Start Thread]) --> InitStream[Open Audio Stream]
    InitStream --> CheckRun{Is Running?}
    
    subgraph AudioLoop [Processing Loop]
        CheckRun -- Yes --> Read[Read 30ms Chunk]
        Read --> VAD{Is Speech?}
        
        %% Speech Detected Path
        VAD -- Yes --> SpeechTrue[Set SpeechDetected = True]
        SpeechTrue --> ResetSil[Reset Silence Counter]
        ResetSil --> Buffer[Append Chunk to Buffer]
        
        %% Silence Path
        VAD -- No --> CheckActive{Was Speech Active?}
        CheckActive -- No --> CheckRun
        
        CheckActive -- Yes --> IncSil[Increment Silence Counter]
        IncSil --> CheckThresh{Silence > Threshold?}
        
        %% CRITICAL CHANGE HERE:
        %% We now buffer the silence if we haven't reached the threshold yet.
        CheckThresh -- No --> Buffer
        
        CheckThresh -- Yes --> Finalize[Finalize Chunk]
    end
    
    Finalize --> Yield[Yield Audio Data]
    Yield --> Transcribe[Transcribe & Output]
    Transcribe --> Clear[Clear Buffer]
    Clear --> ResetFlag[Set SpeechDetected = False]
    ResetFlag --> CheckRun
    
    CheckRun -- No --> Stop([Stop Thread])
```

### 4. Implementation Details

#### Target File: `src/result_thread.py`

We need to modify the `_process_audio_queue` method.

##### Current Code (Lines 232-233)

```python
                elif speech_detected:
                    silent_frame_count += 1
                    # Silent frame is IGNORED here
```

##### Proposed Code

```python
                elif speech_detected:
                    silent_frame_count += 1
                    recording.extend(frame)  # <--- CRITICAL FIX: Keep the silence
```

### 5. Benefits of this Change

1. **Natural Sounding Audio**: The audio passed to Whisper will sound like a normal recording, pauses included.
2. **Improved Accuracy**: Whisper relies on context and pacing. Preserving silence helps it distinguish between "Let's eat, Grandma" and "Let's eat Grandma".
3. **Robustness**: Reduces the chance of words being cut off if the VAD flickers briefly during a soft consonant.

---

## Change 2: Dynamic Silence Threshold

> **Note:** This section outlines a proposed improvement to make the silence threshold dynamic based on the user's speaking pace.

### 1. Problem Analysis: Static Thresholds

#### Current Behavior

The application uses a fixed silence threshold (default 900ms) to determine when a sentence has ended.

#### The Impact

- **Fast Talkers**: May feel the app is too slow to finalize sentences, waiting nearly a second after they stop speaking.
- **Slow Talkers**: May have their sentences cut off prematurely if they pause to think.

### 2. Proposed Solution: Adaptive Threshold

Implement a simple adaptive mechanism that adjusts the silence threshold based on the length of the current speech segment.

#### Logic

- **Short Utterances**: Use a shorter threshold (e.g., 500ms) for quick commands (e.g., "Yes", "No", "Stop").
- **Long Utterances**: Use a longer threshold (e.g., 1000ms-1200ms) for dictation, allowing for natural pauses for thought.

#### Implementation Strategy

1. Track the duration of the current `speech_detected` session.
2. If `duration < 2 seconds`: `silence_threshold = 500ms`
3. If `duration >= 2 seconds`: `silence_threshold = 1000ms`

### 3. Benefits

1. **Responsiveness**: Makes the app feel snappier for short commands.
2. **Forgiveness**: Prevents cutting off users during longer dictation sessions.

---

## Change 3: Input Buffer Flushing

> **Note:** This section addresses an issue where transcribed text is correctly generated but fails to appear fully in the target application until a subsequent key press.

### 1. Problem Analysis: Event Loop Blocking & Buffer Stalls

#### Symptoms

- The terminal shows the correct transcription: `Transcription completed... Post-processed line: "Hello World"`
- The target application (Notepad, Browser) shows: `"Hello Wor"` or nothing at all.
- Pressing any key (e.g., Space) suddenly causes the missing characters to appear.

#### Root Cause

This is a common issue with `pynput` and OS-level input simulation.

1. **Event Loop Blocking**: The `InputSimulator` might be running on the main thread or blocking the event loop, preventing the OS from processing the simulated events immediately.
2. **Missing Flush**: Some applications buffer input events and wait for a "commit" signal (like a space or enter) or a specific time interval.
3. **Race Conditions**: If the simulation happens too fast, the OS input queue might get overwhelmed or desynchronized.

### 2. Proposed Solution: Explicit Flush & Delays

We need to ensure that the input simulation is robust and forces the OS to process the events.

#### Strategy

1. **Add Small Delays**: Introduce a tiny delay between keystrokes (if not already present) to allow the OS to process each event.
2. **Explicit Flush**: Simulate a "dummy" non-printing key event (like `Shift` up/down) at the end of the typing sequence to force the OS to flush its input buffer.
3. **Process Events**: Ensure the Qt event loop processes events after typing.

### 3. Implementation Plan

#### Target File: `src/input_simulation.py`

Modify the `_PynputSimulator.typewrite` method.

#### Proposed Code Changes

```python
    def typewrite(self, text):
        text = self._perform_word_replacements(text)
        
        # 1. Type the text
        self.keyboard.type(text)
        
        # 2. Force Flush Strategy
        # Simulate a harmless key press to flush the OS buffer
        # This is often required for applications that buffer input (like some editors or remote desktops)
        time.sleep(0.01) 
        self.keyboard.touch(Key.shift, False) # Release shift just in case
        time.sleep(0.01)
```

### 4. Benefits

- **Reliability**: Ensures 100% of the transcribed text appears in the target window.
- **Consistency**: Fixes the "missing characters" bug across different applications.

---

## Change 4: Input Simulation Queueing

> **Note:** This section addresses the "lost words" issue where the application fails to input text if multiple transcriptions arrive in quick succession.

### 4.1 Problem Analysis: Overlapping Input Calls

#### Symptoms

- User speaks "Sentence A".
- User immediately speaks "Sentence B".
- Result: "Sentence A" is typed, but "Sentence B" is partially or completely lost, or mixed with A.

#### Root Cause: Race Conditions in Input Simulator

The `InputSimulator.typewrite` method is likely being called by the main thread (via `viappApp.resultSignal`) while a previous `typewrite` operation is still in progress.

1. **Reentrancy**: `typewrite` is not thread-safe. If called again while typing, it might interrupt the current loop or be blocked by the OS event queue.
2. **Blocking UI**: If `typewrite` runs on the main UI thread, it freezes the app. If it runs on a thread but without a queue, simultaneous calls can conflict.

### 4.2 Proposed Solution: Serialized Input Queue

We need to ensure that all text to be typed is added to a **Queue**, and a dedicated worker thread processes this queue one item at a time.

#### Architecture

1. **Input Queue**: A thread-safe `Queue` to hold strings to be typed.
2. **Input Worker**: A background thread that:
    - Waits for text in the queue.
    - Types the text.
    - Waits for the typing to finish before processing the next item.

### 4.3 Implementation Plan

#### Target File: `src/input_simulation.py`

1. Modify `_BaseSimulator` or `InputSimulator` to manage a queue and a worker thread.
2. The `typewrite` method should simply `put()` text into the queue and return immediately (non-blocking).
3. A `_process_queue` method runs in a separate thread to handle the actual typing.

#### Proposed Code Structure

```python
import threading
from queue import Queue

class _BaseSimulator:
    def __init__(self):
        self.input_queue = Queue()
        self.worker_thread = threading.Thread(target=self._input_worker, daemon=True)
        self.worker_thread.start()

    def typewrite(self, text):
        # Non-blocking: just add to queue
        self.input_queue.put(text)

    def _input_worker(self):
        while True:
            text = self.input_queue.get()
            try:
                self._do_typewrite(text)
            except Exception as e:
                ConfigManager.console_print(f"Input error: {e}")
            finally:
                self.input_queue.task_done()

    def _do_typewrite(self, text):
        # Actual typing logic (moved from typewrite)
        # ...
```

### 4.4 Benefits

- **Serialized Output**: "Sentence A" will always finish typing before "Sentence B" starts.
- **No Data Loss**: Even if the user speaks faster than the computer can type, the text is safely buffered.
- **Non-Blocking**: The main application remains responsive.
