## Project Explanation: AI Document Organizer

### 1. Summary of Project Purpose and Main Features

The AI Document Organizer is an intelligent application designed to help users automatically organize their digital documents and media files. It leverages advanced AI models, specifically Google Gemini and OpenAI, to analyze file content and create a structured, categorized folder system.

**Main Features:**

*   **AI-Powered Analysis & Categorization:** Utilizes AI to understand the content of various file types and automatically sorts them into logical folders.
*   **Multi-AI Model Support:** Offers flexibility by supporting models from both Google Gemini (e.g., 2.0 Flash, 1.5 Pro) and OpenAI (e.g., GPT-4, GPT-3.5 Turbo). Users can manage API keys and select models within the application.
*   **Extensive File Format Support:**
    *   **Documents:** CSV, Excel, HTML, Markdown, Text, Word.
    *   **Images:** JPG, PNG, GIF, BMP, TIFF, WebP.
    *   **Audio:** MP3, WAV, FLAC, AAC, OGG, M4A.
    *   **Video:** MP4, AVI, MKV, MOV, WMV, WebM, FLV.
*   **Content Extraction:** Automatically extracts text from all supported document and image formats for analysis.
*   **Media Analysis:** Provides detailed analysis for audio and video files, including metadata (duration, bitrate, resolution), audio waveform generation, video thumbnail generation, and audio transcription.
*   **Cloud Storage Integration:** Supports bidirectional synchronization with Google Drive, OneDrive, and Dropbox, including features like conflict resolution, selective sync, and bandwidth control.
*   **Customizable Organization Schemes:** Allows users to import/export organization rules, use predefined templates, or create custom rules for how files should be structured.
*   **Batch Processing & Rate Limiting:** Efficiently processes files in configurable batches and includes controls to manage API rate limits, optimizing performance and costs.

### 2. Explanation of Project Structure (Two Versions)

The project has evolved and effectively exists in two interconnected versions:

*   **Original AI Document Organizer (V1 - Monolithic):** This is the primary user-facing application, with its source code located in the main `src/` directory. It features a complete set of functionalities for document and media organization, including a graphical user interface (GUI) (managed by `src/gui.py`). It's designed as a comprehensive solution for end-users. The `main.py` at the root of the project is the entry point for this version.

*   **AI Document Organizer V2 (Modular, Plugin-Based):** Located in the `ai_document_organizer_v2/` directory, V2 represents a significant architectural redesign. It transitions from a monolithic structure to a highly modular, plugin-based system. This version focuses on extensibility, maintainability, and allows developers to easily add new functionalities (e.g., support for new file formats, new analysis capabilities) through a standardized plugin interface.
    *   **Plugin Architecture:** V2 is built around different types of plugins (Parser, Analyzer, Organizer, Utility).
    *   **V1 Compatibility:** V2 includes a "V1 compatibility layer," suggesting that it can work with or extend the original system, ensuring a smooth transition or integration of features.
    *   **Development Phases:** V2's development is structured in phases, progressively adding capabilities like core architecture, media processing, cloud/database integration, and advanced specialized analysis.

The top-level `README.md` primarily describes the features and structure of the user-facing application (V1), while the `ai_document_organizer_v2/docs/README.md` details the architecture and development roadmap of the more developer-focused, extensible V2.

### 3. Brief Overview of the Technology Stack

*   **Primary Language:** Python (versions 3.8 or higher).
*   **AI Models:**
    *   Google Gemini API
    *   OpenAI API
*   **Media Processing:** FFmpeg is required for audio and video analysis and processing tasks.
*   **User Interface (V1):** Native Windows interface, as indicated by the "Windows-Optimized" description, `src/gui.py`, and packaging for `.exe` distribution.
*   **File Handling:** Supports a wide array of document, image, audio, and video file formats.
*   **Modularity (V2):** Plugin-based architecture for extensibility.

### 4. Description of the Target Audience and Potential Use Cases

*   **Target Audience:**
    *   **End-Users (V1):** Individuals or businesses using Windows (10/11) looking for an automated solution to manage and organize large volumes of digital files. This includes users who want to leverage AI for content-based categorization without needing technical expertise.
    *   **Developers (V2):** Software developers interested in extending the capabilities of the document organizer, creating new plugins for specific file types, integrating new AI services, or building custom document processing workflows.

*   **Potential Use Cases:**
    *   Automatically sorting a messy "Downloads" folder into structured directories based on document content (e.g., invoices, reports, articles).
    *   Organizing multimedia collections by extracting metadata, transcribing audio, and generating thumbnails.
    *   Creating a searchable archive of documents by extracting and indexing their text content.
    *   Integrating personal or business documents with cloud storage providers in an organized manner.
    *   Researchers or analysts who need to process and categorize large datasets of mixed media files.
    *   Developers building custom document management solutions who can leverage V2's plugin architecture as a foundation.
