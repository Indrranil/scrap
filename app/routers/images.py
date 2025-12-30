from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(prefix="/v1/images", tags=["images"])

# Base directory for images - Docker bind mount to ./app/images
IMAGES_BASE_DIR = Path("/app/images")

# Valid image file extensions
VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.ico', '.mp4', '.avi'}


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


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    path: Optional[str] = Query(None, description="Optional relative path to save image (creates directories if needed)")
):
    """Upload an image file to the images directory"""
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No filename provided"
            )

        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in VALID_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed extensions: {', '.join(VALID_IMAGE_EXTENSIONS)}"
            )

        # Determine save path
        if path:
            # Create full path with subdirectory
            save_dir = IMAGES_BASE_DIR / path
            full_path = save_dir / file.filename
        else:
            # Save to root images directory
            save_dir = IMAGES_BASE_DIR
            full_path = IMAGES_BASE_DIR / file.filename

        # Normalize path for security
        full_path = full_path.resolve()
        save_dir = save_dir.resolve()

        # Security check - ensure path is within images directory
        if not str(full_path).startswith(str(IMAGES_BASE_DIR.resolve())):
            raise HTTPException(
                status_code=400,
                detail="Invalid save path - path traversal not allowed"
            )

        # Create directory if it doesn't exist
        save_dir.mkdir(parents=True, exist_ok=True)

        # Check if file already exists
        if full_path.exists():
            raise HTTPException(
                status_code=409,
                detail=f"File already exists: {file.filename}"
            )

        # Save the file
        content = await file.read()
        with open(full_path, "wb") as f:
            f.write(content)

        # Return success response
        relative_path = full_path.relative_to(IMAGES_BASE_DIR)
        return {
            "message": "Image uploaded successfully",
            "filename": file.filename,
            "path": str(relative_path),
            "size": len(content)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading image: {str(e)}"
        )
