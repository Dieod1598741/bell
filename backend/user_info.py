"""사용자 정보 관리 모듈 - storage_path 기반"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from machine_id import get_hardware_uuid


class UserInfoManager:
    """사용자 정보를 storage_path에 저장/관리"""
    
    def __init__(self, storage_path: str):
        """
        Args:
            storage_path: WebView localStorage 저장소 경로
        """
        # Path 객체를 문자열로 저장 (pywebview 직렬화 문제 방지)
        self.storage_path_str = str(storage_path)
        self._storage_path = Path(storage_path)
        self._user_file = self._storage_path / "user_info.json"
        self._status_file = self._storage_path / "user_status.txt"
        self._last_access_file = self._storage_path / "last_access_time.txt"
        
        # 저장소 디렉토리가 없으면 생성
        self._storage_path.mkdir(parents=True, exist_ok=True)
    
    def get_user(self) -> Optional[Dict[str, Any]]:
        """사용자 정보 조회"""
        try:
            if not self._user_file.exists():
                return None
            
            with open(self._user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception as e:
            print(f"[UserInfo] 사용자 정보 조회 실패: {e}")
            return None
    
    def save_user(self, user_data: Dict[str, Any]) -> bool:
        """사용자 정보 저장"""
        try:
            with open(self._user_file, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
            print(f"[UserInfo] 사용자 정보 저장 완료: user_id={user_data.get('id')}")
            return True
        except Exception as e:
            print(f"[UserInfo] 사용자 정보 저장 실패: {e}")
            return False
    
    def update_user(self, user_data: Dict[str, Any]) -> bool:
        """사용자 정보 업데이트 (기존 데이터와 병합)"""
        try:
            existing = self.get_user() or {}
            updated = {**existing, **user_data}
            return self.save_user(updated)
        except Exception as e:
            print(f"[UserInfo] 사용자 정보 업데이트 실패: {e}")
            return False
    
    def delete_user(self) -> bool:
        """사용자 정보 삭제"""
        try:
            if self._user_file.exists():
                self._user_file.unlink()
                print("[UserInfo] 사용자 정보 삭제 완료")
            return True
        except Exception as e:
            print(f"[UserInfo] 사용자 정보 삭제 실패: {e}")
            return False
    
    def get_user_status(self) -> Optional[str]:
        """사용자 상태 조회"""
        try:
            if not self._status_file.exists():
                return None
            
            with open(self._status_file, 'r', encoding='utf-8') as f:
                status = f.read().strip()
                return status if status else None
        except Exception as e:
            print(f"[UserInfo] 사용자 상태 조회 실패: {e}")
            return None
    
    def save_user_status(self, status: str) -> bool:
        """사용자 상태 저장"""
        try:
            with open(self._status_file, 'w', encoding='utf-8') as f:
                f.write(status)
            print(f"[UserInfo] 사용자 상태 저장 완료: {status}")
            return True
        except Exception as e:
            print(f"[UserInfo] 사용자 상태 저장 실패: {e}")
            return False
    
    def delete_user_status(self) -> bool:
        """사용자 상태 삭제"""
        try:
            if self._status_file.exists():
                self._status_file.unlink()
                print("[UserInfo] 사용자 상태 삭제 완료")
            return True
        except Exception as e:
            print(f"[UserInfo] 사용자 상태 삭제 실패: {e}")
            return False
    
    def get_login_settings(self, hardware_id: str) -> Optional[Dict[str, Any]]:
        """하드웨어 ID별 로그인 설정 조회"""
        try:
            settings_file = self._storage_path / f"login_settings_{hardware_id}.json"
            if not settings_file.exists():
                return None
            
            with open(settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception as e:
            print(f"[UserInfo] 로그인 설정 조회 실패: {e}")
            return None
    
    def save_login_settings(self, hardware_id: str, settings: Dict[str, Any]) -> bool:
        """하드웨어 ID별 로그인 설정 저장"""
        try:
            settings_file = self._storage_path / f"login_settings_{hardware_id}.json"
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            print(f"[UserInfo] 로그인 설정 저장 완료: hardware_id={hardware_id}")
            return True
        except Exception as e:
            print(f"[UserInfo] 로그인 설정 저장 실패: {e}")
            return False
    
    def delete_login_settings(self, hardware_id: str) -> bool:
        """하드웨어 ID별 로그인 설정 삭제"""
        try:
            settings_file = self._storage_path / f"login_settings_{hardware_id}.json"
            if settings_file.exists():
                settings_file.unlink()
                print(f"[UserInfo] 로그인 설정 삭제 완료: hardware_id={hardware_id}")
            return True
        except Exception as e:
            print(f"[UserInfo] 로그인 설정 삭제 실패: {e}")
            return False
    
    def update_last_access_time(self) -> bool:
        """마지막 접근 시간 업데이트 (하트비트)"""
        try:
            current_time = datetime.now().isoformat()
            with open(self._last_access_file, 'w', encoding='utf-8') as f:
                f.write(current_time)
            return True
        except Exception as e:
            print(f"[UserInfo] 마지막 접근 시간 업데이트 실패: {e}")
            return False
    
    def get_last_access_time(self) -> Optional[datetime]:
        """마지막 접근 시간 조회"""
        try:
            if not self._last_access_file.exists():
                return None
            
            with open(self._last_access_file, 'r', encoding='utf-8') as f:
                time_str = f.read().strip()
                if time_str:
                    return datetime.fromisoformat(time_str)
            return None
        except Exception as e:
            print(f"[UserInfo] 마지막 접근 시간 조회 실패: {e}")
            return None
    
    def should_set_offline(self, timeout_minutes: int = 5) -> bool:
        """마지막 접근 시간을 기준으로 오프라인으로 설정해야 하는지 확인"""
        try:
            last_access = self.get_last_access_time()
            if not last_access:
                return True  # 접근 시간이 없으면 오프라인으로 처리
            
            elapsed = (datetime.now() - last_access).total_seconds() / 60
            return elapsed > timeout_minutes
        except Exception as e:
            print(f"[UserInfo] 오프라인 확인 실패: {e}")
            return True
    
    def update_last_access_time(self) -> bool:
        """마지막 접근 시간 업데이트"""
        try:
            current_time = datetime.now().isoformat()
            with open(self._last_access_file, 'w', encoding='utf-8') as f:
                f.write(current_time)
            return True
        except Exception as e:
            print(f"[UserInfo] 마지막 접근 시간 업데이트 실패: {e}")
            return False
    
    def get_last_access_time(self) -> Optional[datetime]:
        """마지막 접근 시간 조회"""
        try:
            if not self._last_access_file.exists():
                return None
            
            with open(self._last_access_file, 'r', encoding='utf-8') as f:
                time_str = f.read().strip()
                if time_str:
                    return datetime.fromisoformat(time_str)
            return None
        except Exception as e:
            print(f"[UserInfo] 마지막 접근 시간 조회 실패: {e}")
            return None
    
    def should_set_offline(self, timeout_minutes: int = 5) -> bool:
        """마지막 접근 시간을 기준으로 오프라인으로 설정해야 하는지 확인"""
        try:
            last_access = self.get_last_access_time()
            if not last_access:
                return True  # 접근 시간이 없으면 오프라인으로 처리
            
            elapsed = (datetime.now() - last_access).total_seconds() / 60
            return elapsed > timeout_minutes
        except Exception as e:
            print(f"[UserInfo] 오프라인 확인 실패: {e}")
            return True

