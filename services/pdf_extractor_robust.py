"""
CareBridge AI - Robust PDF Extractor
Handles PDFs with multiple fallback strategies
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# PDF Libraries will be lazy-loaded in methods

# Text cleaning
import unicodedata


class RobustPDFExtractor:
    """
    Multi-strategy PDF text extractor with automatic fallback
    """
    
    def __init__(self):
        self.extraction_methods = [
            self._extract_with_pdfplumber,  # Best for most PDFs
            self._extract_with_pypdf2,      # Fallback 1
            self._extract_with_ocr,         # Fallback 2 (scanned PDFs)
        ]
    
    def extract_text(self, pdf_path: str) -> Tuple[str, str]:
        """
        Extract text from PDF using multiple strategies
        
        Returns:
            (extracted_text, method_used)
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Try each method until one succeeds
        for method in self.extraction_methods:
            try:
                text = method(str(pdf_path))
                if text and len(text.strip()) > 100:  # Minimum text threshold
                    method_name = method.__name__
                    print(f"✅ Successfully extracted with {method_name}")
                    return self._clean_text(text), method_name
            except Exception as e:
                print(f"⚠️ {method.__name__} failed: {e}")
                continue
        
        raise Exception("All PDF extraction methods failed. PDF might be corrupted or protected.")
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """
        Method 1: pdfplumber (BEST - handles tables, layout)
        """
        import pdfplumber
        text_parts = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text
                page_text = page.extract_text()
                
                if page_text:
                    text_parts.append(f"\n--- Page {page_num} ---\n")
                    text_parts.append(page_text)
                
                # Extract tables separately
                tables = page.extract_tables()
                if tables:
                    for table_idx, table in enumerate(tables, 1):
                        text_parts.append(f"\n[Table {table_idx}]\n")
                        text_parts.append(self._format_table(table))
        
        return "\n".join(text_parts)
    
    def _extract_with_pypdf2(self, pdf_path: str) -> str:
        """
        Method 2: PyPDF2 (FALLBACK 1 - simple text extraction)
        """
        import PyPDF2
        text_parts = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                
                if page_text:
                    text_parts.append(f"\n--- Page {page_num} ---\n")
                    text_parts.append(page_text)
        
        return "\n".join(text_parts)
    
    def _extract_with_ocr(self, pdf_path: str) -> str:
        """
        Method 3: OCR (FALLBACK 2 - for scanned PDFs)
        Converts PDF to images, then uses Tesseract OCR
        """
        import pytesseract
        from pdf2image import convert_from_path
        print("📸 Using OCR (this may take 1-2 minutes for scanned PDFs)...")
        
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=300)
        
        text_parts = []
        
        for page_num, image in enumerate(images, 1):
            # OCR the image
            page_text = pytesseract.image_to_string(image, lang='eng')
            
            if page_text:
                text_parts.append(f"\n--- Page {page_num} ---\n")
                text_parts.append(page_text)
        
        return "\n".join(text_parts)
    
    def _format_table(self, table: List[List[str]]) -> str:
        """
        Convert table to readable text format
        """
        formatted_rows = []
        
        for row in table:
            # Filter out None values and join with spacers
            clean_row = [str(cell).strip() if cell else "" for cell in row]
            # Remove repeated empty cells
            if any(clean_row):
                formatted_rows.append(" | ".join(clean_row))
        
        return "\n".join(formatted_rows)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text with focus on preserving clause structure
        """
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Preserve double newlines for paragraph separation
        # but remove excess empty lines (3+)
        text = re.sub(r'[\r\n]{3,}', '\n\n', text)
        
        # Remove common PDF artifacts (e.g., weird spacing between letters)
        # but be careful not to merge intended spaces.
        # This regex fixes "W a i t i n g   P e r i o d" -> "Waiting Period"
        text = re.sub(r'(?<=[a-zA-Z])\s(?=[a-zA-Z]\s)', '', text)
        
        # Remove page markers
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'--- Page \d+ ---', '', text)
        
        # Strip trailing/leading whitespace per line
        lines = [line.strip() for line in text.split('\n')]
        
        return "\n".join(lines).strip()


# ============================================
# INSTALLATION INSTRUCTIONS
# ============================================

def install_dependencies():
    """
    Run this once to install all required packages
    """
    packages = [
        "pdfplumber",           # Best PDF parser
        "PyPDF2",              # Fallback parser
        "pytesseract",         # OCR engine
        "pdf2image",           # Convert PDF to images
        "Pillow",              # Image processing
    ]
    
    print("Installing dependencies...")
    import subprocess
    
    for package in packages:
        subprocess.check_call(["pip", "install", package, "--break-system-packages"])
    
    print("\n✅ All dependencies installed!")
    print("\n⚠️ IMPORTANT: You also need to install Tesseract OCR:")
    print("   Ubuntu: sudo apt-get install tesseract-ocr")
    print("   Mac: brew install tesseract")
    print("   Windows: Download from GitHub")


# ============================================
# USAGE EXAMPLE
# ============================================

def test_extractor():
    """
    Test the PDF extractor
    """
    extractor = RobustPDFExtractor()
    
    # Test with your policy PDF
    pdf_path = "/path/to/your/policy.pdf"
    
    try:
        text, method = extractor.extract_text(pdf_path)
        
        print(f"\n{'='*60}")
        print(f"Extraction Method: {method}")
        print(f"Extracted Text Length: {len(text)} characters")
        print(f"{'='*60}\n")
        
        # Show first 1000 characters
        print(text[:1000])
        print("\n... (truncated)")
        
        # Save to file
        with open("extracted_policy.txt", "w") as f:
            f.write(text)
        
        print("\n✅ Full text saved to: extracted_policy.txt")
        
        return text
        
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        return None


if __name__ == "__main__":
    # Uncomment to install dependencies
    # install_dependencies()
    
    # Test the extractor
    test_extractor()
