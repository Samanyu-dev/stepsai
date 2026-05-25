import fitz  # PyMuPDF
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extracts raw text content from PDF binary streams using PyMuPDF (fitz).
    PyMuPDF offers extremely fast, robust text-layer decoding.
    
    Args:
        pdf_bytes (bytes): The binary stream of the uploaded PDF file.
        
    Returns:
        str: Cleaned, compiled text from the PDF.
    """
    try:
        # Open PDF from byte stream
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_content = []
        
        # Iterate and extract text from every page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text_content.append(page.get_text())
            
        doc.close()
        
        # Merge all page text and clean leading/trailing whitespace
        full_text = "\n".join(text_content).strip()
        
        if not full_text:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The uploaded PDF has no readable text layout. "
                    "Ensure it contains an actual text layer (is not a raw scanned image/screenshot)."
                )
            )
            
        return full_text
        
    except Exception as e:
        logger.error(f"Failed to parse PDF using PyMuPDF parser: {str(e)}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Internal parser failed to decode the document structure: {str(e)}"
        )
