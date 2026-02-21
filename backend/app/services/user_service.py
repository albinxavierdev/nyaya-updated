import os
from typing import Optional
from uuid import UUID
from app.schemas.user_schema import UserAuth, UserUpdate
from app.models.user_model import User
from app.core.security import get_password, verify_password
from pymongo.errors import DuplicateKeyError
from bson import Binary
from dotenv import load_dotenv
from app.db import async_mongodb

# Load environment variables
load_dotenv()


class UserService:
    @property
    def users_collection(self):
        return async_mongodb.db.users

    async def create_user(self, user: UserAuth) -> User:
        user_obj = User(
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            hashed_password=get_password(user.password),
            role="user",  # Set default role to "user"
        )
        user_dict = user_obj.to_mongo()

        try:
            result = await self.users_collection.insert_one(user_dict)
            user_dict["_id"] = result.inserted_id
            return User.from_mongo(user_dict)
        except DuplicateKeyError:
            raise ValueError("Username or email already exists")

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        user = await self.get_user_by_email(email=email)
        if not user:
            return None
        if not verify_password(password=password, hashed_pass=user.hashed_password):
            return None
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        user_dict = await self.users_collection.find_one({"email": email})
        return User.from_mongo(user_dict) if user_dict else None

    async def get_or_create_user_google(
        self, email: str, first_name: Optional[str] = None, last_name: Optional[str] = None
    ) -> User:
        """Get user by email, or create one with a placeholder password for Google sign-in."""
        user = await self.get_user_by_email(email=email)
        if user:
            return user
        placeholder = get_password(os.urandom(32).hex())
        user_obj = User(
            email=email,
            hashed_password=placeholder,
            first_name=first_name or "",
            last_name=last_name or "",
            role="user",
        )
        user_dict = user_obj.to_mongo()
        try:
            await self.users_collection.insert_one(user_dict)
            return user_obj
        except DuplicateKeyError:
            return await self.get_user_by_email(email=email)

    async def get_user_by_id(self, id: UUID) -> Optional[User]:
        user_dict = await self.users_collection.find_one(
            {"user_id": Binary.from_uuid(id)}
        )
        return User.from_mongo(user_dict) if user_dict else None

    async def update_user(self, id: UUID, data: UserUpdate) -> User:
        update_data = data.model_dump(exclude_unset=True)
        result = await self.users_collection.update_one(
            {"user_id": Binary.from_uuid(id)}, {"$set": update_data}
        )

        if result.modified_count == 0:
            raise ValueError("User not found")

        updated_user = await self.get_user_by_id(id)
        return updated_user


user_service = UserService()
