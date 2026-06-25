from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

ROLE_LEVELS = {
    "consulta": 1,
    "operador": 3,
    "supervisor": 7,
    "admin": 9,
}


def hash_password(password: str, allow_weak: bool = False) -> str:
    if not password or (not allow_weak and len(password) < 8):
        raise ValueError("La contrasena debe tener al menos 8 caracteres.")
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not plain_password or not password_hash:
        return False
    return pwd_context.verify(plain_password, password_hash)


def role_from_security_level(level: int) -> str:
    if level >= 9:
        return "admin"
    if level >= 7:
        return "supervisor"
    if level >= 3:
        return "operador"
    return "consulta"


def role_allows(user_role: str, required_role: str) -> bool:
    return ROLE_LEVELS.get(user_role, 0) >= ROLE_LEVELS.get(required_role, 0)
