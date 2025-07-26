# Text Extraction Service

A flexible service for extracting text from PDF documents via URL or local file paths. The service supports multiple extraction methods and can be easily extended with custom extractors.

## Features

- **Multiple Extraction Methods**: Support for PyPDF, PyMuPDF, and combined extraction
- **URL Support**: Extract text directly from PDF URLs
- **Local File Support**: Extract text from local PDF files
- **Extensible**: Easy to add custom extraction methods
- **Error Handling**: Comprehensive error handling and logging
- **File Output**: Optional saving of extracted text to files

## Installation

The service uses existing dependencies from the project:
- `pypdf` - For PyPDF extraction method
- `pymupdf` - For PyMuPDF 