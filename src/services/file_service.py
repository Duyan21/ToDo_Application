import os
import logging
from datetime import datetime
from typing import Optional, Tuple
from werkzeug.utils import secure_filename
from src.repositories import get_file_repository
from src.database.models import File

logger = logging.getLogger(__name__)


class FileService:
    ALLOWED_EXTENSIONS = {"csv"}
    
    @staticmethod
    def is_allowed_file(filename: str) -> bool:
        """Check if file extension is allowed."""
        return "." in filename and filename.rsplit(".", 1)[1].lower() in FileService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def upload_file(user_id: int, uploaded_file, workspace_root: str) -> Tuple[Optional[File], str]:
        """
        Upload a file and save it to the database.
        Returns (file_record, message)
        """
        try:
            if not uploaded_file or uploaded_file.filename == "":
                return None, "Vui lòng chọn file CSV để tải lên."
            
            if not FileService.is_allowed_file(uploaded_file.filename):
                return None, "Chỉ hỗ trợ file CSV."
            
            # Create upload folder if it doesn't exist
            upload_folder = os.path.join(workspace_root, "upload")
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_filename = secure_filename(uploaded_file.filename)
            saved_filename = f"{timestamp}_{original_filename}"
            save_path = os.path.join(upload_folder, saved_filename)
            
            # Save file to disk
            uploaded_file.save(save_path)
            
            # Create file record in database
            file_record = get_file_repository().create(
                user_id=user_id,
                filename=original_filename,
                file_path=os.path.relpath(save_path, workspace_root),
                is_imported=False,
            )
            
            logger.info("File %s uploaded for user %s.", original_filename, user_id)
            return file_record, f"Tải lên file thành công: {original_filename}"
            
        except Exception as e:
            logger.error("Error uploading file: %s", str(e))
            return None, f"Lỗi khi tải lên file: {str(e)}"
    
    @staticmethod
    def get_files_for_user(user_id: int, filter_type: str = "all") -> list:
        """Get files for a specific user with optional filter."""
        file_repository = get_file_repository()
        return file_repository.get_files_for_user_with_filter(user_id, filter_type)
