import sys
import os
from pathlib import Path

# backend 폴더를 경로에 추가
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from db_manager import DBManager

def check_users():
    db = DBManager()
    query = "SELECT id, name, nick_nm, permission, del_yn FROM users"
    result, error = db.execute_query(query)
    
    if error:
        print(f"Error fetching users: {error}")
        return
        
    print(f"Total users found: {len(result)}")
    print("-" * 50)
    for user in result:
        print(f"ID: {user['id']} | Name: {user['name']} | Nick: {user['nick_nm']} | Perm: {user['permission']} | Deleted: {user['del_yn']}")
    print("-" * 50)

if __name__ == "__main__":
    check_users()
