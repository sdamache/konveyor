import os
import sys
import logging
from io import BytesIO
from dotenv import load_dotenv

# Add project root to sys.path to allow importing konveyor modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from konveyor.core.documents.document_service import DocumentService
from azure.core.exceptions import HttpResponseError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

def test_pdf_parsing():
    logging.info("--- Starting PDF Parsing Test ---")
    
    # Initialize DocumentService
    try:
        document_service = DocumentService()
        logging.info("Successfully initialized DocumentService")
    except Exception as e:
        logging.error(f"Failed to initialize DocumentService: {e}", exc_info=True)
        return

    # Define path to the sample PDF file
    pdf_file_path = os.path.join(
        project_root,
        'konveyor',
        'core',     # Correct path segment should be 'core'
        'documents',
        'tests',
        'test_files',
        'sample.pdf'
    )

    if not os.path.exists(pdf_file_path):
        logging.error(f"PDF file not found at: {pdf_file_path}")
        return

    logging.info(f"Attempting to parse PDF: {pdf_file_path}")

    try:
        # Open the file in binary mode
        with open(pdf_file_path, 'rb') as f:
            # Read content and wrap in BytesIO
            file_content = f.read()
            file_obj = BytesIO(file_content)
            file_obj.name = os.path.basename(pdf_file_path) # Add filename for clarity
            
            logging.info(f"Read {len(file_content)} bytes from {file_obj.name}. Calling parse_file...")
            
            # Call the parse_file method
            content, metadata = document_service.parse_file(
                file_obj=file_obj,
                content_type='application/pdf'
            )
            
            logging.info("--- PDF Parsing Successful! ---")
            logging.info(f"Extracted Metadata: {metadata}")
            logging.info(f"Extracted Content (first 500 chars):\n{content[:500]}...")
            
    except HttpResponseError as hre:
        logging.error("--- PDF Parsing Failed (Azure Error) ---", exc_info=False) # Don't need full traceback here
        logging.error(f"Status Code: {hre.status_code}")
        logging.error(f"Error Code: {hre.error.code if hasattr(hre, 'error') and hasattr(hre.error, 'code') else 'N/A'}")
        logging.error(f"Message: {hre.message}")
        if hasattr(hre.error, 'innererror') and hre.error.innererror:
             logging.error(f"Inner Error Code: {hre.error.innererror.get('code', 'N/A')}")
             logging.error(f"Inner Error Message: {hre.error.innererror.get('message', 'N/A')}")
             
    except Exception as e:
        logging.error("--- PDF Parsing Failed (General Error) ---", exc_info=True)

if __name__ == "__main__":
    test_pdf_parsing()
