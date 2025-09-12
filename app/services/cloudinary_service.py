import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException, status
from app.config import settings
import uuid
import os
from io import BytesIO

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=settings.cloudinary_secure
)

class CloudinaryService:
    """Service for handling file uploads to Cloudinary"""
    
    @staticmethod
    async def upload_file(
        file: UploadFile,
        folder: str = "cycle",
        public_id: Optional[str] = None,
        transformation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Cloudinary
        
        Args:
            file: The uploaded file
            folder: The folder to upload to in Cloudinary
            public_id: Custom public ID for the file
            transformation: Image transformation options
            
        Returns:
            Dict containing the upload result
        """
        try:
            # Generate a unique public_id if not provided
            if not public_id:
                file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
                public_id = f"{folder}/{uuid.uuid4()}{file_extension}"
            
            # Read file content
            file_content = await file.read()
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file_content,
                public_id=public_id,
                folder=folder,
                resource_type="auto",  # Automatically detect file type
                transformation=transformation
            )
            
            return {
                "success": True,
                "public_id": upload_result["public_id"],
                "secure_url": upload_result["secure_url"],
                "url": upload_result["url"],
                "format": upload_result.get("format"),
                "bytes": upload_result.get("bytes"),
                "width": upload_result.get("width"),
                "height": upload_result.get("height")
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    @staticmethod
    async def upload_verification_document(
        file: UploadFile,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Upload a verification document with specific settings
        
        Args:
            file: The uploaded verification document
            user_id: The ID of the user uploading the document
            
        Returns:
            Dict containing the upload result
        """
        # Define transformation for verification documents
        transformation = {
            "quality": "auto",
            "fetch_format": "auto",
            "flags": "attachment"  # Force download instead of display
        }
        
        return await CloudinaryService.upload_file(
            file=file,
            folder=f"verification/{user_id}",
            transformation=transformation
        )
    
    @staticmethod
    async def upload_bike_photo(
        file: UploadFile,
        bike_id: str,
        photo_index: int = 0
    ) -> Dict[str, Any]:
        """
        Upload a bike photo with optimization
        
        Args:
            file: The uploaded bike photo
            bike_id: The ID of the bike
            photo_index: Index of the photo (for multiple photos)
            
        Returns:
            Dict containing the upload result
        """
        # Define transformation for bike photos
        transformation = {
            "quality": "auto",
            "fetch_format": "auto",
            "width": 800,
            "height": 600,
            "crop": "limit"
        }
        
        return await CloudinaryService.upload_file(
            file=file,
            folder=f"bikes/{bike_id}",
            public_id=f"photo_{photo_index}",
            transformation=transformation
        )
    
    @staticmethod
    async def delete_file(public_id: str) -> Dict[str, Any]:
        """
        Delete a file from Cloudinary
        
        Args:
            public_id: The public ID of the file to delete
            
        Returns:
            Dict containing the deletion result
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            return {
                "success": result.get("result") == "ok",
                "result": result
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}"
            )
    
    @staticmethod
    def get_optimized_url(
        public_id: str,
        transformation: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate an optimized URL for a Cloudinary resource
        
        Args:
            public_id: The public ID of the resource
            transformation: Transformation options
            
        Returns:
            Optimized URL
        """
        if transformation:
            return cloudinary.CloudinaryImage(public_id).build_url(transformation=transformation)
        else:
            return cloudinary.CloudinaryImage(public_id).build_url()
    
    @staticmethod
    def get_thumbnail_url(public_id: str, size: int = 150) -> str:
        """
        Generate a thumbnail URL for an image
        
        Args:
            public_id: The public ID of the image
            size: The size of the thumbnail
            
        Returns:
            Thumbnail URL
        """
        transformation = {
            "width": size,
            "height": size,
            "crop": "fill",
            "quality": "auto",
            "fetch_format": "auto"
        }
        return CloudinaryService.get_optimized_url(public_id, transformation)

# Create a singleton instance
cloudinary_service = CloudinaryService()
