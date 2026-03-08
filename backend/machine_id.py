"""하드웨어 UUID 가져오기 (플랫폼별)"""
import subprocess
import platform
from platform_detector import PlatformDetector

# UUID 캐싱 (한 번만 가져오기)
_cached_uuid = None


def get_hardware_uuid_macos() -> str:
    """macOS에서 하드웨어 UUID 가져오기"""
    try:
        # 방법 1: system_profiler 사용
        result = subprocess.run(
            ['system_profiler', 'SPHardwareDataType'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'Hardware UUID' in line or 'UUID' in line:
                    # "Hardware UUID: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" 형식
                    parts = line.split(':')
                    if len(parts) >= 2:
                        uuid = parts[1].strip()
                        if uuid:
                            return uuid
        
        # 방법 2: ioreg 사용 (대체 방법)
        result = subprocess.run(
            ['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'IOPlatformUUID' in line:
                    # "    |   "IOPlatformUUID" = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"" 형식
                    if '=' in line:
                        parts = line.split('=')
                        if len(parts) >= 2:
                            uuid = parts[1].strip().strip('"')
                            if uuid:
                                return uuid
    except Exception as e:
        print(f"[machine_id] macOS UUID 가져오기 실패: {e}")
    
    return None


def get_hardware_uuid_windows() -> str:
    """Windows에서 하드웨어 UUID 가져오기"""
    try:
        # WMI를 통해 가져오기
        result = subprocess.run(
            ['wmic', 'csproduct', 'get', 'uuid'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                line = line.strip()
                # UUID 형식 확인 (XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX)
                if line and len(line) == 36 and line.count('-') == 4:
                    return line
    except Exception as e:
        print(f"[machine_id] Windows UUID 가져오기 실패: {e}")
    
    return None


def get_hardware_uuid_linux() -> str:
    """Linux에서 하드웨어 UUID 가져오기"""
    try:
        # 방법 1: /etc/machine-id 사용
        try:
            with open('/etc/machine-id', 'r') as f:
                machine_id = f.read().strip()
                if machine_id:
                    return machine_id
        except:
            pass
        
        # 방법 2: DMI를 통해 가져오기
        result = subprocess.run(
            ['dmidecode', '-s', 'system-uuid'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            uuid = result.stdout.strip()
            if uuid:
                return uuid
    except Exception as e:
        print(f"[machine_id] Linux UUID 가져오기 실패: {e}")
    
    return None


def get_hardware_uuid() -> str:
    """플랫폼별 하드웨어 UUID 가져오기 (캐싱됨)"""
    global _cached_uuid
    
    # 캐시된 값이 있으면 반환
    if _cached_uuid is not None:
        return _cached_uuid
    
    # UUID 가져오기
    if PlatformDetector.is_macos():
        uuid = get_hardware_uuid_macos()
    elif PlatformDetector.is_windows():
        uuid = get_hardware_uuid_windows()
    elif PlatformDetector.is_linux():
        uuid = get_hardware_uuid_linux()
    else:
        print(f"[machine_id] 지원하지 않는 플랫폼: {platform.system()}")
        _cached_uuid = None
        return None
    
    # 결과 캐싱 및 로그 출력 (한 번만)
    if uuid:
        _cached_uuid = uuid
        print(f"[machine_id] 하드웨어 UUID: {uuid}")
        return uuid
    else:
        _cached_uuid = None
        print(f"[machine_id] 하드웨어 UUID를 가져올 수 없습니다")
        return None


if __name__ == '__main__':
    """테스트"""
    uuid = get_hardware_uuid()
    if uuid:
        print(f"✅ 하드웨어 UUID: {uuid}")
    else:
        print("❌ 하드웨어 UUID를 가져올 수 없습니다")




