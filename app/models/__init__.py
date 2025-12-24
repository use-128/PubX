# app/models/__init__.py

from .account_model import Account
from .publication_record_model import PublicationRecord

# 兼容 Pydantic v2 / v1 的前向引用处理

try:
    # ✅ Pydantic v2 推荐用法
    Account.model_rebuild()
    PublicationRecord.model_rebuild()
except AttributeError:
    # ✅ 如果环境里是 Pydantic v1，则退回到老的 API
    Account.update_forward_refs()
    PublicationRecord.update_forward_refs()

__all__ = [
    "Account",
    "PublicationRecord",
]
