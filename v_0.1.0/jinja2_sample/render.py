from jinja2 import Environment, FileSystemLoader

# カレントディレクトリからテンプレートをロード
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('child.html')

# テンプレートをレンダリング
rendered_html = template.render()

# 結果をHTMLファイルに出力
with open('output.html', 'w', encoding='utf-8') as f:
    f.write(rendered_html)

print("レンダリング完了！output.htmlをブラウザで開いて確認してください。")
# 実行は　python render.py
