import logging
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from src.common.errors import (
    AuthError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
)
from src.repositories import get_user_repository
from src.dto.user_dto import UserDTO, UserLoginDTO, UserRegisterDTO

logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def register(dto: UserRegisterDTO) -> UserDTO:
        if not dto.name:
            raise AuthError("Tên không được để trống")
        user_repository = get_user_repository()
        try:
            user = user_repository.create(
                name=dto.name,
                email=dto.email,
                password_hash=generate_password_hash(dto.password),
            )
        except IntegrityError:
            raise EmailAlreadyExistsError("Email đã tồn tại")
        except Exception as e:
            logger.error("Error during registration: %s", str(e))
            raise AuthError("Đăng ký thất bại, vui lòng thử lại sau")

        logger.info("New user registered: %s", dto.email)
        return UserDTO.from_model(user)

    @staticmethod
    def signin(dto: UserLoginDTO) -> UserDTO:
        user_repository = get_user_repository()
        user = user_repository.get_by_email(dto.email)
        if not user or not check_password_hash(user.password_hash, dto.password):
            logger.warning("Failed signin attempt for email: %s", dto.email)
            raise InvalidCredentialsError("Email hoặc mật khẩu không đúng")

        logger.info("User signed in: %s", dto.email)
        return UserDTO.from_model(user)
