"""플랫폼 감지 모듈"""
import platform
from enum import Enum

class Platform(Enum):
    """플랫폼 타입"""
    MACOS = "macos"
    WINDOWS = "windows"
    LINUX = "linux"
    UNKNOWN = "unknown"

class PlatformDetector:
    """플랫폼 감지기"""
    
    @staticmethod
    def detect() -> Platform:
        """현재 플랫폼 감지"""
        system = platform.system()
        
        if system == 'Darwin':
            return Platform.MACOS
        elif system == 'Windows':
            return Platform.WINDOWS
        elif system == 'Linux':
            return Platform.LINUX
        else:
            return Platform.UNKNOWN
    
    @staticmethod
    def is_macos() -> bool:
        """macOS인지 확인"""
        return PlatformDetector.detect() == Platform.MACOS
    
    @staticmethod
    def is_windows() -> bool:
        """Windows인지 확인"""
        return PlatformDetector.detect() == Platform.WINDOWS
    
    @staticmethod
    def is_linux() -> bool:
        """Linux인지 확인"""
        return PlatformDetector.detect() == Platform.LINUX
    
    @staticmethod
    def get_platform_name() -> str:
        """플랫폼 이름 반환"""
        return PlatformDetector.detect().value










