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
    import re
    uuid_pattern = re.compile(r'^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$')

    # 방법 1: wmic (Windows 10 이하)
    try:
        result = subprocess.run(
            ['wmic', 'csproduct', 'get', 'uuid'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if uuid_pattern.match(line):
                    return line
    except Exception:
        pass

    # 방법 2: PowerShell (Windows 11+ 에서 wmic deprecated 대응)
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             '(Get-CimInstance Win32_ComputerSystemProduct).UUID'],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=0x08000000  # CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            uuid = result.stdout.strip()
            if uuid_pattern.match(uuid):
                return uuid
    except Exception as e:
        print(f"[machine_id] PowerShell UUID 실패: {e}")

    # 방법 3: MAC 주소로 안정적 ID 생성 (마지막 폴백)
    try:
        import uuid as uuid_module
        import hashlib
        mac = uuid_module.getnode()
        # MAC + 고정 salt로 sha256 → UUID 형식으로 변환
        h = hashlib.sha256(f"bell_mac_{mac}".encode()).hexdigest()
        stable_id = f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"
        print(f"[machine_id] MAC 기반 폴백 ID 사용: {stable_id}")
        return stable_id
    except Exception as e:
        print(f"[machine_id] MAC 기반 폴백 실패: {e}")

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
    
    # 결과 캐싱 (성공 시만 캐싱, 실패 시 재시도 가능)
    if uuid:
        _cached_uuid = uuid
        print(f"[machine_id] 하드웨어 UUID: {uuid}")
        return uuid
    else:
        # null은 캐싱하지 않음 → 다음 호출 시 재시도
        print(f"[machine_id] 하드웨어 UUID를 가져올 수 없습니다")
        return None


if __name__ == '__main__':
    """테스트"""
    uuid = get_hardware_uuid()
    if uuid:
        print(f"✅ 하드웨어 UUID: {uuid}")
    else:
        print("❌ 하드웨어 UUID를 가져올 수 없습니다")




