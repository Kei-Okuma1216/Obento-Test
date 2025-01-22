# __init__.py

# package変数
# これらは my_package.package_variable や 
# my_package.package_function() としてアクセスできます。
package_variable = "this is a package-level variable"
def package_function():
    return "this is a package-level function"

# パッケージ内で公開するモジュールや関数を指定
from .local_jwt_module import create_jwt, create_jwt, SECRET_KEY, private_key, load_private_key, sign_message,ALGORITHM 
from .init_module import init_database, conn