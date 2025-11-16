This is Solition to one of the cases presented at 2025 AIESEC hackathon in NU.
Contributors: Nadyrkhan Shyntemir, Kaltayev Ernur, Aitbayev Aslanbek

A powerful AI-powered document analysis system that automatically detects signatures, QR codes, and stamps in PDF documents and images.
🚀 Features

    Signature Detection: Identifies handwritten and digital signatures using transformer models

    QR Code Detection: Locates and decodes QR codes in documents

    Stamp Detection: Detects official stamps and seals (model configurable)

    PDF Support: Processes multi-page PDF documents automatically

    REST API: FastAPI-based API for easy integration

    Batch Processing: Test multiple files simultaneously

📊 Performance Results

Based on testing with 58 real-world PDF documents:

    58 files successfully processed

    167 pages analyzed

    70 signatures detected

    102 QR codes found

    280 seconds total processing time

    100% success rate

🛠 Installation
Prerequisites

    Python 3.8+

    pip package manager

Quick Start

    Clone the repository

    git clone <repository-url>
    cd aiesec_hackathon


    Create virtual environment

    python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies

cd backend/app
pip install -r requirements.txt

 Usage
Method 1: Direct Testing (Recommended for batch processing)

Run the test script to analyze all PDFs in a directory:

python test.py


The script will:

    Process all PDF files in selected_output/pdfs/

    Generate detailed JSON results

    Show real-time progress

    Save results to test_results.json

Method 2: Web API

Start the FastAPI server:

python main.py

The API will be available at http://localhost:8000
API Endpoints

    POST /api/detect/all - Detect all elements in a file

    POST /api/detect/signatures - Detect only signatures

    POST /api/detect/qr-codes - Detect only QR codes

    POST /api/detect/stamps - Detect only stamps

    GET /api/health - Check API status

Example API Request

curl -X POST "http://localhost:8000/api/detect/all" \
  -F "file=@document.pdf"


   Project Structure

aiesec_hackathon/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI server
│   │   ├── detection_services.py   # Core detection logic
│   │   ├── requirements.txt        # Python dependencies
│   │   └── services/
│   │       └── test.py            # Batch testing script
│   └── models/                    # YOLO model files (optional)
├── selected_output/
│   └── pdfs/                      # Test PDF documents
└── README.md


 Configuration
Model Settings

The system uses three AI models:

    Signature Detection: mdefrance/yolos-base-signature-detection

    QR Code Detection: qrdet library

    Stamp Detection: Custom YOLO model (path: models/best.pt)

Environment Variables

Create a .env file for configuration:

UPLOAD_DIR=uploads
MODELS_DIR=models
ENV=development


Output Format
JSON Response Example

{
  "success": true,
  "file_type": "pdf",
  "total_pages": 9,
  "pages": [
    {
      "page": 1,
      "detections": {
        "signatures": [...],
        "qr_codes": [...],
        "stamps": [...]
      },
      "counts": {
        "signatures": 2,
        "qr_codes": 1,
        "stamps": 0
      }
    }
  ],
  "total_counts": {
    "signatures": 70,
    "qr_codes": 102,
    "stamps": 0
  }
}


Deployment
Local Development

uvicorn main:app --reload --host 0.0.0.0 --port 8000

Production Deployment

The application is ready for deployment on:

    Railway

    Heroku

    Render

    Docker environments

See deployment configuration files in the repository.
🧪 Testing

Run the comprehensive test suite:


cd backend/app/services
python test.py


This will process all documents and generate a detailed performance report.
📈 Performance

    Average processing time: 1.5-2 seconds per page

    Signature accuracy: High precision on clear signatures

    QR code detection: Near-perfect detection rate

    Multi-page PDFs: Automatic page-by-page analysis

🔍 Detection Details
Signature Detection

    Uses YOLOS transformer model

    Detects both handwritten and digital signatures

    Provides bounding boxes and confidence scores


    Check the troubleshooting section below

    Review the API documentation at /docs when server is running

    Create an issue in the repository

QR Code Detection

    Uses optimized QRDet library

    Handles multiple QR codes per page

    Works on various sizes and qualities

Stamp Detection

    Configurable YOLO model

    Requires custom training data

    Easily extendable for different stamp types
🔮 Future Enhancements

    Improved stamp detection models

    Additional document types support

    Cloud storage integration

    Real-time processing

    Mobile application

    Advanced analytics dashboard

StampNSign Detector - Automating document verification with AI precision.


Future Enhancements

    Improved stamp detection models

    Additional document types support

    Cloud storage integration

    Real-time processing

    Mobile application

    Advanced analytics dashboard