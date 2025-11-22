# Viapp Process Flow Diagrams

> **Note:** This document contains **Mermaid** diagrams. To view them:
>
> - **In VS Code**: Install the [Markdown Preview Mermaid Support](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid) extension.
> - **On GitHub**: These diagrams will render automatically.
> - **Online**: Copy the code blocks into the [Mermaid Live Editor](https://mermaid.live/).

This document visualizes the optimized workflows of the Viapp application.

## 1. Application Initialization Flow

This diagram groups the startup process into logical phases: Configuration, Setup, and Initialization.

```mermaid
graph TD
    Start([Application Start]) --> ConfigPhase
    
    subgraph ConfigPhase [Configuration Phase]
        direction TB
        InitMgr[Init ConfigManager] --> LoadSchema[Load Schema]
        LoadSchema --> LoadDef[Load Defaults]
        LoadDef --> LoadUser[Load User Config]
        LoadUser --> Merge[Merge Configs]
    end
    
    Merge --> CheckExist{Config Exists?}
    
    CheckExist -- No --> SetupPhase
    CheckExist -- Yes --> InitPhase
    
    subgraph SetupPhase [First Run Setup]
        direction TB
        ShowSettings[Show Settings Window] --> UserSave[User Saves Settings]
        UserSave --> Restart[Restart Application]
    end
    
    subgraph InitPhase [Component Initialization]
        direction TB
        InitComps[Init Components] --> InitInput[Init InputSimulator]
        InitInput --> InitKeys[Init KeyListener]
        InitKeys --> InitModel[Create Whisper Model]
        InitModel --> InitUI[Init Main Window]
    end
    
    InitUI --> Ready([App Ready / Idle])
```

## 2. Audio Processing & VAD Logic

This flowchart details the `ResultThread` loop. **Note:** The current implementation now buffers silent frames during active speech to preserve natural prosody.

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
        
        %% New Behavior: Silent frames ARE buffered
        CheckThresh -- No --> BufferSil[Append Silence to Buffer]
        BufferSil --> CheckRun
        CheckThresh -- Yes --> Finalize[Finalize Chunk]
    end
    
    Finalize --> Yield[Yield Audio Data]
    Yield --> Transcribe[Transcribe & Output]
    Transcribe --> Clear[Clear Buffer]
    Clear --> ResetFlag[Set SpeechDetected = False]
    ResetFlag --> CheckRun
    
    CheckRun -- No --> Stop([Stop Thread])
```

## 3. Transcription Sequence

This sequence diagram groups participants by layer (UI, Logic, Core) to clearly show the interaction boundaries, including the **asynchronous input queue**.

```mermaid
sequenceDiagram
    participant User
    participant UI as MainWindow
    participant App as ViappApp
    participant Thread as ResultThread
    participant Model as WhisperModel
    participant Input as InputSimulator
    participant Worker as InputWorker

    Note over User, UI: **Activation Phase**
    User->>App: Hotkey Pressed (Ctrl+Alt+K)
    App->>UI: set_state("recording")
    UI-->>User: Show Red Icon
    App->>Thread: start()
    
    Note over Thread: **Recording Phase**
    loop Audio Stream
        Thread->>Thread: Capture & VAD Check
    end
    
    Note over Thread, Model: **Processing Phase**
    Thread->>Thread: Silence Threshold Met
    Thread->>App: statusSignal("transcribing")
    App->>UI: set_state("transcribing")
    
    Thread->>Model: transcribe(audio_chunk)
    activate Model
    Model-->>Thread: "Transcribed Text"
    deactivate Model
    
    Note over Thread, Input: **Output Phase**
    Thread->>App: partialResultSignal("Transcribed Text")
    App->>UI: update_label("...Text")
    
    Thread->>App: resultSignal("Transcribed Text")
    App->>Input: typewrite("Transcribed Text")
    
    Note right of Input: **Non-Blocking Queue**
    Input->>Worker: Queue.put(text)
    Input-->>App: Return immediately
    
    activate Worker
    Worker->>Input: typingStarted.emit()
    Input->>App: Signal("typing")
    App->>UI: set_state("typing")
    
    loop Character by Character
        Worker->>User: Simulate Keystrokes
    end
    
    Worker->>Input: typingFinished.emit()
    deactivate Worker
    Input->>App: Signal("idle")
    App->>UI: set_state("idle")
```

## 4. Audio Device Error Handling Strategy

This diagram uses a cleaner layout to show the fallback mechanism for audio devices.

```mermaid
graph TD
    Start([Request Stream]) --> ConfigID[Get Configured Device ID]
    ConfigID --> Attempt1{Open Stream?}
    
    Attempt1 -- Success --> Success([Return Stream])
    Attempt1 -- Fail --> Log1[Log Error]
    
    Log1 --> Query[Query System Devices]
    Query --> Find[Find First Input Device]
    Find --> Found{Device Found?}
    
    Found -- No --> Fatal([Fatal Error])
    Found -- Yes --> Log2[Log Fallback Device]
    
    Log2 --> Attempt2{Open Fallback?}
    Attempt2 -- Success --> Success
    Attempt2 -- Fail --> Fatal
```

## 5. Input Simulation Selection Logic

This diagram uses a Left-to-Right flow to visualize the decision tree for selecting the input method.

```mermaid
graph LR
    Start([Init Simulator]) --> Method{Config Method?}
    
    %% Pynput Path
    Method -- "pynput" --> Pynput[Use Pynput]
    
    %% Ydotool Path
    Method -- "ydotool" --> LinuxCheck1{Is Linux?}
    LinuxCheck1 -- No --> Warn1[Log Warning] --> Pynput
    LinuxCheck1 -- Yes --> ToolCheck1{ydotool installed?}
    ToolCheck1 -- Yes --> Ydotool[Use Ydotool]
    ToolCheck1 -- No --> Warn2[Log Error] --> Pynput
    
    %% Auto Path
    Method -- "auto" --> LinuxCheck2{Is Linux?}
    LinuxCheck2 -- No --> Pynput
    LinuxCheck2 -- Yes --> ToolCheck2{ydotool installed?}
    ToolCheck2 -- Yes --> Ydotool
    ToolCheck2 -- No --> Pynput
```
