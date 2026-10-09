"""
ClaimGuard Storage Manager
Handles file storage abstraction (local filesystem or AWS S3)
Allows seamless switching between development and production
"""
import os
import json
from datetime import datetime
from pathlib import Path


class StorageManager:
    """Abstract storage manager for local and cloud storage"""
    
    def __init__(self, storage_type='local', config=None):
        self.storage_type = storage_type
        self.config = config or {}
        
        if storage_type == 'local':
            self.backend = LocalStorageBackend(self.config)
        elif storage_type == 's3':
            self.backend = S3StorageBackend(self.config)
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")
    
    def save_file(self, claim_id, document_type, file_content, filename):
        """Save a file and return file path/key"""
        return self.backend.save_file(claim_id, document_type, file_content, filename)
    
    def get_file(self, claim_id, file_path):
        """Retrieve file content"""
        return self.backend.get_file(claim_id, file_path)
    
    def delete_file(self, claim_id, file_path):
        """Delete a file"""
        return self.backend.delete_file(claim_id, file_path)
    
    def list_files(self, claim_id):
        """List all files for a claim"""
        return self.backend.list_files(claim_id)
    
    def get_file_url(self, claim_id, file_path, expires_in=3600):
        """Get public/presigned URL for file access"""
        return self.backend.get_file_url(claim_id, file_path, expires_in)


class LocalStorageBackend:
    """Local filesystem storage for development"""
    
    def __init__(self, config):
        self.base_path = config.get('upload_folder', './uploads')
        Path(self.base_path).mkdir(parents=True, exist_ok=True)
    
    def save_file(self, claim_id, document_type, file_content, filename):
        """Save file to local filesystem"""
        claim_dir = Path(self.base_path) / str(claim_id)
        claim_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{document_type}_{timestamp}_{filename}"
        file_path = claim_dir / unique_filename
        
        # Write file
        file_path.write_bytes(file_content)
        
        return {
            'path': str(file_path),
            'key': f"{claim_id}/{unique_filename}",
            'filename': filename,
            'size': len(file_content),
            'storage_type': 'local'
        }
    
    def get_file(self, claim_id, file_path):
        """Retrieve file from local filesystem"""
        full_path = Path(file_path)
        if full_path.exists():
            return full_path.read_bytes()
        return None
    
    def delete_file(self, claim_id, file_path):
        """Delete file from local filesystem"""
        full_path = Path(file_path)
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    
    def list_files(self, claim_id):
        """List all files for a claim"""
        claim_dir = Path(self.base_path) / str(claim_id)
        if not claim_dir.exists():
            return []
        
        files = []
        for file_path in claim_dir.glob('*'):
            files.append({
                'path': str(file_path),
                'filename': file_path.name,
                'size': file_path.stat().st_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            })
        return files
    
    def get_file_url(self, claim_id, file_path, expires_in=3600):
        """Get file URL (local endpoint)"""
        return f"/api/files/{claim_id}/{os.path.basename(file_path)}"


class S3StorageBackend:
    """AWS S3 cloud storage for production"""
    
    def __init__(self, config):
        try:
            import boto3
        except ImportError:
            raise ImportError("boto3 not installed. Install with: pip install boto3")
        
        self.bucket = config.get('bucket')
        self.region = config.get('region', 'us-east-1')
        
        # Initialize S3 client
        self.s3 = boto3.client(
            's3',
            region_name=self.region,
            aws_access_key_id=config.get('access_key'),
            aws_secret_access_key=config.get('secret_key')
        )
    
    def save_file(self, claim_id, document_type, file_content, filename):
        """Save file to S3"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"claims/{claim_id}/{document_type}_{timestamp}_{filename}"
        
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=file_content,
                ContentType='application/octet-stream',
                Metadata={
                    'claim_id': str(claim_id),
                    'document_type': document_type,
                    'original_filename': filename
                }
            )
            
            return {
                'path': f"s3://{self.bucket}/{s3_key}",
                'key': s3_key,
                'filename': filename,
                'size': len(file_content),
                'storage_type': 's3'
            }
        except Exception as e:
            raise Exception(f"Failed to upload to S3: {str(e)}")
    
    def get_file(self, claim_id, s3_key):
        """Retrieve file from S3"""
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=s3_key)
            return response['Body'].read()
        except Exception as e:
            raise Exception(f"Failed to download from S3: {str(e)}")
    
    def delete_file(self, claim_id, s3_key):
        """Delete file from S3"""
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=s3_key)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete from S3: {str(e)}")
    
    def list_files(self, claim_id):
        """List all files for a claim in S3"""
        try:
            prefix = f"claims/{claim_id}/"
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'filename': obj['Key'].split('/')[-1],
                        'size': obj['Size'],
                        'modified': obj['LastModified'].isoformat()
                    })
            return files
        except Exception as e:
            raise Exception(f"Failed to list S3 files: {str(e)}")
    
    def get_file_url(self, claim_id, s3_key, expires_in=3600):
        """Get presigned URL for S3 file"""
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")
