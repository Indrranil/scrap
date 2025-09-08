from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

router = APIRouter(prefix="/v1/images", tags=["images"])

# Base directory for images - now inside app/
IMAGES_BASE_DIR = Path(__file__).parent.parent / "images"

# Valid image file extensions
VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.ico'}


@router.get("/{image_path:path}")
async def get_image(
    image_path: str,
    folder: Optional[str] = Query(None, description="Optional subfolder within images directory")
):
    """Get image file from the images directory"""
    try:
        # Construct the full path
        if folder:
            full_path = IMAGES_BASE_DIR / folder / image_path
        else:
            full_path = IMAGES_BASE_DIR / image_path

        # Normalize the path to prevent directory traversal attacks
        full_path = full_path.resolve()

        # Ensure the path is within the images directory (security check)
        if not str(full_path).startswith(str(IMAGES_BASE_DIR.resolve())):
            raise HTTPException(
                status_code=400,
                detail="Invalid image path - path traversal not allowed"
            )

        # Check if file exists
        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(
                status_code=404,
                detail=f"Image not found: {image_path}"
            )

        # Check if it's a valid image file
        if full_path.suffix.lower() not in VALID_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type - only image files are allowed"
            )

        # Return the image file
        return FileResponse(
            path=str(full_path),
            media_type=f"image/{full_path.suffix[1:]}",
            filename=full_path.name
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving image: {str(e)}"
        )


@router.get("/")
async def list_images(
    folder: Optional[str] = Query(None, description="Optional subfolder to list images from")
):
    """List all images in the images directory or specified subfolder"""
    try:
        # Construct the directory path
        target_dir = IMAGES_BASE_DIR / folder if folder else IMAGES_BASE_DIR

        # Check if directory exists
        if not target_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Directory not found: {folder or 'images'}"
            )

        # Get all image files
        images = []
        for file_path in target_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in VALID_IMAGE_EXTENSIONS:
                relative_path = file_path.relative_to(target_dir)
                images.append({
                    "name": file_path.name,
                    "path": str(relative_path),
                    "size": file_path.stat().st_size,
                    "extension": file_path.suffix.lower()
                })

        return {
            "directory": str(target_dir),
            "total": len(images),
            "images": images
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing images: {str(e)}"
        )
