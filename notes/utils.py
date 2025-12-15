"""
미디어 파일 검증 유틸리티
"""

import mimetypes
from pathlib import Path


# 허용된 파일 타입 및 크기 제한
ALLOWED_IMAGE_TYPES = {
    'image/png': ['.png'],
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/webp': ['.webp'],
    'image/gif': ['.gif'],
}

ALLOWED_AUDIO_TYPES = {
    'audio/mpeg': ['.mp3'],
    'audio/wav': ['.wav'],
    'audio/ogg': ['.ogg'],
    'audio/webm': ['.webm'],
    'audio/mp4': ['.m4a'],
    'audio/x-m4a': ['.m4a'],
}

ALLOWED_VIDEO_TYPES = {
    'video/mp4': ['.mp4'],
    'video/webm': ['.webm'],
    'video/ogg': ['.ogv'],
    'video/quicktime': ['.mov'],
}

# 파일 크기 제한 (bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB


def validate_file_type(file, allowed_types):
    """
    파일 타입 검증
    Returns: (is_valid, file_type, mime_type, error_message)
    """
    if not file:
        return False, None, None, '파일이 없습니다.'
    
    # 파일명에서 확장자 추출
    filename = file.name.lower()
    ext = Path(filename).suffix
    
    # MIME 타입 확인
    mime_type = file.content_type
    
    # MIME 타입이 없으면 파일명으로 추정
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(filename)
    
    if not mime_type:
        return False, None, None, '파일 타입을 확인할 수 없습니다.'
    
    # 허용된 타입 확인
    if mime_type not in allowed_types:
        return False, None, None, f'지원하지 않는 파일 타입입니다: {mime_type}'
    
    # 확장자 확인
    if ext not in allowed_types[mime_type]:
        return False, None, None, f'파일 확장자가 MIME 타입과 일치하지 않습니다.'
    
    return True, mime_type, mime_type, None


def validate_image(file):
    """
    이미지 파일 검증
    Returns: (is_valid, mime_type, error_message)
    """
    is_valid, file_type, mime_type, error = validate_file_type(file, ALLOWED_IMAGE_TYPES)
    if not is_valid:
        return False, None, error
    
    # 파일 크기 확인
    if file.size > MAX_IMAGE_SIZE:
        return False, None, f'이미지 파일 크기는 최대 {MAX_IMAGE_SIZE // (1024*1024)}MB입니다.'
    
    return True, mime_type, None


def validate_audio(file):
    """
    음성 파일 검증
    Returns: (is_valid, mime_type, error_message)
    """
    is_valid, file_type, mime_type, error = validate_file_type(file, ALLOWED_AUDIO_TYPES)
    if not is_valid:
        return False, None, error
    
    # 파일 크기 확인
    if file.size > MAX_AUDIO_SIZE:
        return False, None, f'음성 파일 크기는 최대 {MAX_AUDIO_SIZE // (1024*1024)}MB입니다.'
    
    return True, mime_type, None


def validate_video(file):
    """
    영상 파일 검증
    Returns: (is_valid, mime_type, error_message)
    """
    is_valid, file_type, mime_type, error = validate_file_type(file, ALLOWED_VIDEO_TYPES)
    if not is_valid:
        return False, None, error
    
    # 파일 크기 확인
    if file.size > MAX_VIDEO_SIZE:
        return False, None, f'영상 파일 크기는 최대 {MAX_VIDEO_SIZE // (1024*1024)}MB입니다.'
    
    return True, mime_type, None


def get_file_type_from_mime(mime_type):
    """
    MIME 타입으로 파일 타입 결정
    Returns: 'image', 'audio', 'video' 또는 None
    """
    if mime_type in ALLOWED_IMAGE_TYPES:
        return 'image'
    elif mime_type in ALLOWED_AUDIO_TYPES:
        return 'audio'
    elif mime_type in ALLOWED_VIDEO_TYPES:
        return 'video'
    return None


