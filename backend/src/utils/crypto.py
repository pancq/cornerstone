from cryptography.fernet import Fernet
import os
import base64

def _find_existing_key(env_path: str) -> str | None:
    """从 .env 文件中查找现有的密钥"""
    if not os.path.exists(env_path):
        return None
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('CREDENTIAL_SECRET_KEY='):
                return line.split('=', 1)[1]
    
    return None

# 从环境变量或 .env 文件读取密钥，若不存在则自动生成
def get_or_generate_key() -> bytes:
    # 1. 首先尝试从环境变量读取
    secret_key = os.environ.get("CREDENTIAL_SECRET_KEY")
    
    # 2. 如果环境变量中没有，从 .env 文件读取
    if not secret_key:
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        secret_key = _find_existing_key(env_path)
    
    if secret_key:
        return base64.urlsafe_b64decode(secret_key)
    
    # 3. 生成新密钥
    key = Fernet.generate_key()
    # 写入 .env 文件
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    with open(env_path, 'a') as f:
        f.write(f"\nCREDENTIAL_SECRET_KEY={base64.urlsafe_b64encode(key).decode()}\n")
    
    return key

# 全局 Fernet 实例
_fernet = Fernet(get_or_generate_key())

def encrypt_password(plain_text: str) -> str:
    """加密密码，返回base64字符串"""
    if not plain_text:
        return ""
    return _fernet.encrypt(plain_text.encode()).decode()

def decrypt_password(cipher_text: str) -> str:
    """解密密码，返回明文。解密失败时抛出异常（密钥不匹配或数据损坏）"""
    if not cipher_text:
        return ""
    try:
        return _fernet.decrypt(cipher_text.encode()).decode()
    except Exception as e:
        raise ValueError(f"凭证解密失败，请检查密钥是否正确: {e}") from e