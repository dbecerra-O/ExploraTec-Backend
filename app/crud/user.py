from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

class UserCRUD:
    def get_users(self, db: Session, user_id: int) -> Optional[User]:
        """Obtiene un usuario por ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_user_not_admin(db: Session, skip: int = 0, limit: int = 100):
        return db.query(User).filter(User.is_admin == False).offset(skip).limit(limit).all()
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Obtiene un usuario por email"""
        return db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Obtiene un usuario por username"""
        return db.query(User).filter(User.username == username).first()
    
    def get_user_by_username_or_email(self, db: Session, identifier: str) -> Optional[User]:
        """Obtiene un usuario por username o email"""
        return db.query(User).filter(
            or_(User.username == identifier, User.email == identifier)
        ).first()
    
    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Obtiene una lista de usuarios"""
        return db.query(User).offset(skip).limit(limit).all()
    
    def create_user(self, db: Session, user: UserCreate) -> User:
        """Crea un nuevo usuario"""
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,
            is_active=user.is_active,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def create_admin_user(self, db: Session, user: UserCreate) -> User:
        """Crea un nuevo usuario administrador"""
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,
            is_active=user.is_active,
            is_admin=True,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def update_user(self, db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Actualiza un usuario"""
        db_user = self.get_user(db, user_id)
        if not db_user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def delete_user(self, db: Session, user_id: int) -> bool:
        """Elimina un usuario"""
        db_user = self.get_user(db, user_id)
        if not db_user:
            return False
        
        db.delete(db_user)
        db.commit()
        return True
    
    def authenticate_user(self, db: Session, identifier: str, password: str) -> Optional[User]:
        """Autentica un usuario"""
        user = self.get_user_by_username_or_email(db, identifier)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

# Instancia del CRUD
user_crud = UserCRUD()