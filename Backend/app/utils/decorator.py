
# utils/decorator.py

# カスタムデコレーターを定義
# @log_decoratorを関数の上に記述すると、関数の前後にログを出力する
from functools import wraps
import functools
import inspect
import warnings


def log_decorator(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        print(f"- {func.__name__} 前")
        result = await func(*args, **kwargs)
        print(f"- {func.__name__} 後")
        return result

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        print(f"- {func.__name__} 前")
        result = func(*args, **kwargs)
        print(f"- {func.__name__} 後")
        return result

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

# デプリケーション警告を出すデコレーター
def deprecated(func):
    """This is a decorator to mark functions as deprecated."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"{func.__name__} is deprecated and will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2
        )
        return func(*args, **kwargs)
    return wrapper