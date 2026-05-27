import logging
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from src.database.models import User, db
from src.dto.user_dto import UserDTO, UserLoginDTO, UserRegisterDTO

logger = logging.getLogger(__name__)


class AuthError(Exception):
    pass

class EmailAlreadyExistsError(AuthError):
    pass

class InvalidCredentialsError(AuthError):
    pass


class AuthService:

    @staticmethod
    def register(dto: UserRegisterDTO) -> UserDTO:
        if not dto.name:
            raise AuthError("Tên không được để trống")

        user = User(
            name=dto.name,
            email=dto.email,
            password_hash=generate_password_hash(dto.password),
        )
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise EmailAlreadyExistsError("Email đã tồn tại")

        logger.info("New user registered: %s", dto.email)
        return UserDTO.from_model(user)

    @staticmethod
    def signin(dto: UserLoginDTO) -> UserDTO:
        user = User.query.filter_by(email=dto.email).first()
        if not user or not check_password_hash(user.password_hash, dto.password):
            logger.warning("Failed signin attempt for email: %s", dto.email)
            raise InvalidCredentialsError("Email hoặc mật khẩu không đúng")

        logger.info("User signed in: %s", dto.email)
        return UserDTO.from_model(user)
