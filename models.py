# models.py
import uuid
import time
import logging
from typing import List, Dict, Optional, Any
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)

class User:
    def __init__(self, username: str, password_hash: str, user_id: Optional[str] = None, is_admin: bool = False):
        self.user_id = user_id if user_id else str(uuid.uuid4())
        self.username = username
        self.password_hash = password_hash
        self.is_admin = is_admin

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"user_id": self.user_id, "username": self.username, "is_admin": self.is_admin}

class UserManager:
    def __init__(self):
        self.users_by_id: Dict[str, User] = {}
        self.users_by_username: Dict[str, User] = {}
        # Add some test users
        self.add_user("admin", "admin123", is_admin=True)
        self.add_user("test", "test123")

    def add_user(self, username: str, password: str, is_admin: bool = False) -> Optional[User]:
        if username in self.users_by_username:
            logger.warning(f"Attempt to add existing username: {username}")
            return None
        password_hash = generate_password_hash(password)
        new_user = User(username, password_hash, is_admin=is_admin)
        self.users_by_id[new_user.user_id] = new_user
        self.users_by_username[new_user.username] = new_user
        logger.info(f"User '{username}' added successfully.")
        return new_user

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.users_by_username.get(username)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.users_by_id.get(user_id)

    def update_password(self, username: str, new_password: str) -> bool:
        user = self.get_user_by_username(username)
        if user:
            user.password_hash = generate_password_hash(new_password)
            logger.info(f"Password updated for user '{username}'.")
            return True
        logger.warning(f"Attempt to update password for non-existent user: {username}")
        return False

    def delete_user(self, username: str) -> bool:
        user = self.get_user_by_username(username)
        if user:
            if user.username == "admin":
                logger.warning("Attempt to delete admin user blocked.")
                return False
            del self.users_by_id[user.user_id]
            del self.users_by_username[user.username]
            logger.info(f"User '{username}' deleted.")
            return True
        logger.warning(f"Attempt to delete non-existent user: {username}")
        return False

    def get_all_users(self) -> List[Dict]:
        return [user.to_dict() for user in self.users_by_id.values()]

class ResultStorage:
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}

    def save_result(self, user_id: str, result_data: Dict[str, Any]) -> str:
        result_id = str(uuid.uuid4())
        result_data['result_id'] = result_id
        result_data['user_id'] = user_id
        result_data['timestamp'] = time.time()
        self.results[result_id] = result_data
        logger.info(f"Result '{result_id}' saved for user '{user_id}'.")
        return result_id

    def get_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        return self.results.get(result_id)

    def get_results_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        user_results = [res for res in self.results.values() if res['user_id'] == user_id]
        return sorted(user_results, key=lambda x: x['timestamp'], reverse=True)

    def get_all_results(self) -> List[Dict[str, Any]]:
        all_results = list(self.results.values())
        return sorted(all_results, key=lambda x: x['timestamp'], reverse=True)