# src/tools/vision_tools.py
# VisionInspector (detective) tools for analysing visual evidences.

import os
from typing import Dict, List

import fitz  # PyMuPDF


class VisionError(Exception):
    """Custom exception for VisionInspector analysis errors."""


def extract_pdf_images(pdf_path: str) -> List[Dict]:
    """
    Extract embedded images from a PDF file.

    Args:
        pdf_path (str): Path to the PDF report.

    Returns:
        List[Dict]: Metadata for each image, including page number and size.
    """
    figures = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            images = page.get_images(full=True)
            for img_index, img in enumerate(images, start=1):
                xref = img[0]
                info = doc.extract_image(xref)
                figures.append(
                    {
                        "page": page_num + 1,
                        "index": img_index,
                        "width": info.get("width"),
                        "height": info.get("height"),
                        "ext": info.get("ext"),
                    }
                )
    except Exception as e:
        raise VisionError(f"Failed to extract images from PDF: {e}") from e
    return figures


def scan_repo_images(repo_path: str) -> List[str]:
    """
    Scan a repository directory for static image files.

    Args:
        repo_path (str): Path to the cloned repository.

    Returns:
        List[str]: Relative paths of image files found.
    """
    image_files = []
    valid_exts = {".png", ".jpg", ".jpeg", ".svg"}
    for root, _, files in os.walk(repo_path):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts:
                rel_path = os.path.relpath(os.path.join(root, f), repo_path)
                image_files.append(rel_path)
    return image_files


def analyse_visual_evidence(pdf_path: str, repo_path: str) -> Dict:
    """
    Analyse visual evidence from both PDF and repository.

    Args:
        pdf_path (str): Path to interim/final report PDF.
        repo_path (str): Path to cloned repository.

    Returns:
        Dict: Structured evidence including figures and repo images.
    """
    pdf_figures = extract_pdf_images(pdf_path)
    repo_images = scan_repo_images(repo_path)

    visual_flags = {
        "pdf_has_figures": bool(pdf_figures),
        "repo_has_images": bool(repo_images),
        "uml_detected": any("uml" in img.lower() for img in repo_images),
        "charts_detected": any("chart" in img.lower() for img in repo_images),
    }

    return {
        "pdf_figures": pdf_figures,
        "repo_images": repo_images,
        "visual_flags": visual_flags,
    }
