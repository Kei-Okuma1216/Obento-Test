# __init__.py

# package変数
# これらは my_package.package_variable や 
# my_package.package_function() としてアクセスできます。
package_variable = "this is a package-level variable"
def package_function():
    return "this is a package-level function"

# パッケージ内で公開するモジュールや関数を指定
from .jwt_module import create_jwt, create_jwt, SECRET_KEY, package_variable, package_function, private_key,load_private_key

"""
この関数はparam1とparam2を受け取り、結果を返します。
:param param1: 第一のパラメータ
:param param2: 第二のパラメータ
:return: 計算結果
"""
