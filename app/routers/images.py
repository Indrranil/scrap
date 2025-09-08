from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

router = APIRouter(prefix="/v1/images", tags=["images"])

# Base directory for images - now inside app/
IMAGES_BASE_DIR = Path(__file__).parent.parent / "images"

# Valid image file extensions
VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.ico'}


@router.get("/")
async def get_image(
    path: str = Query(..., description="Relative path to image file from images directory")
):
    """Get image file using relative path from images directory"""
    try:
        # Construct the full path from the relative path
        full_path = IMAGES_BASE_DIR / path

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
                detail=f"Image not found: {path}"
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
