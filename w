[33mcommit d3b333af4dd78b61b62148d4af7985ff25e1fd87[m[33m ([m[1;36mHEAD[m[33m -> [m[1;32mmain[m[33m, [m[1;31morigin/main[m[33m, [m[1;31morigin/HEAD[m[33m)[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Feb 18 15:21:06 2025 +0900

    最終注文のCookieのmax-ageは正常に設定できた

[33mcommit 6f8a62071e2bddf1a8041ded7dbbeed26e8df8ce[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Feb 18 14:13:54 2025 +0900

    UserもShopも注文表示できた。しかしCookieは一週間後の期限

[33mcommit 4a652029dd5aa1a2291eeb9619fd9e2e8433c177[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Feb 15 13:03:13 2025 +0900

    0.0.0.0 to 192.168.3.19 modified

[33mcommit 138788bd2234ad43e564d28416709641db2c5ea7[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 28 13:55:48 2025 +0900

    send_requestにしたが/todayでタイムアウトになる

[33mcommit 00d7e1fda5392abaf1dc9f0995b364fb0a9fd595[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Mon Jan 27 15:27:44 2025 +0900

    Method Not Allowedになる。order-cofirm.htmlまで行くが

[33mcommit 43addb75dba864f3e2aa40f735584812f61a6728[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Mon Jan 27 15:12:37 2025 +0900

    login key error

[33mcommit 5d763f94cb6fbf0c981315718483ae9a98214c4b[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Mon Jan 27 13:38:14 2025 +0900

    userにtokenまで更新できた

[33mcommit 2a82e43372476dc160b297c90c13048888cbfc85[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Mon Jan 27 12:01:58 2025 +0900

    payload['exe']でエラー

[33mcommit 3982c9c4f7c4fb19d19ff449064df37ffcc9fd04[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Jan 25 15:24:45 2025 +0900

    非同期エラー

[33mcommit 10868bc91a38233d29e0aeb82b354b6ff458d8a6[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Jan 25 15:09:56 2025 +0900

    Userテーブルが作れない

[33mcommit a173829eff1c82da4c985c6d3db386b1d6474d3c[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Jan 25 13:29:47 2025 +0900

    login.htmlまとめた。しかし/registerが残った

[33mcommit f368a39daa1a842fecce56ddf75e03a4293deac7[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Jan 25 11:37:03 2025 +0900

    ChatGPTに聞いて、login.htmlをわけた

[33mcommit c9628465590907b343a8871abb79dbe7ebf6f37b[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Jan 25 10:46:56 2025 +0900

    やっと正常にOrdersが挿入された

[33mcommit d6d4738a42dc8b958b3e3bfd09559559bdcae9a3[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Fri Jan 24 15:12:46 2025 +0900

    やはりselect_today_ordersが取得できない

[33mcommit f84a00d6f085377b63976eb8bc2f8706a65d87c7[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Fri Jan 24 14:44:57 2025 +0900

    ordersが空っぽ

[33mcommit 37996e6bbc61b7aae9bf8ffaa17f1b5e030246af[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Fri Jan 24 13:50:32 2025 +0900

    権限2が読めた。
    
    しかし/todayにアクセスできず。以下のエラーあり。
    INFO:     127.0.0.1:64498 - "POST /today HTTP/1.1" 405 Method Not Allowed
    method not allowed

[33mcommit d9edb62828fcbb7af52bf0467c715a642b36c0bc[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Fri Jan 24 11:39:16 2025 +0900

    make Cookie Clear Page
    
    CookieのClearページ作った。INSERT Userで重複は取り消しにした。次にやるのは# Please enter the commit message for your changes. Lines starting

[33mcommit 18fa44be807fa85912fe45c8f5cb74bab08c80de[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Fri Jan 24 10:15:57 2025 +0900

    tokenチェックページ別遷移する作業前

[33mcommit 9d547074caf4f050fe69327b99a16b07a019730f[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 23 15:11:58 2025 +0900

    Ordersテーブルが生成できず。それとorders変数にJSON文字列入らず

[33mcommit 83b78d4682bc8f63c8fa6bf3ab77ec7fb23a54d4[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 23 13:16:52 2025 +0900

    autoincrement order_idの重複エラー

[33mcommit b5ad41ac3930b31a388b1cadec6afa0a4b76346e[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 23 10:09:16 2025 +0900

    init_module.py is name changed

[33mcommit f164a2b8aaeb43895a1a6cd3d0751515bde21620[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 22 15:10:44 2025 +0900

    DBBrowser directory added

[33mcommit 28458c4d6cdcb3a718ae45549aee2af35ee050ca[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 22 15:10:03 2025 +0900

    ignore file edited

[33mcommit 815d51040c0c58fc5b88fc62823dd0c3ddd3ac61[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 22 15:09:12 2025 +0900

    ここで権限を判定できないか？

[33mcommit 074df34f7329cf0685173f95d7a04516864f65ff[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 22 14:39:31 2025 +0900

    storeの注文一覧画面が完成した
    
    store_orders_today.htmlに表示する３行のデータをmain.pyからJSONで渡すことに成功した。
    include table.htmlにして内側のテーブルに表示している。

[33mcommit d221b3d097b81c4af03601a16add0a16001a57f8[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 22 13:37:38 2025 +0900

    tutorial

[33mcommit 8de1ebc0a99b944a9327803a81d1824193efdff4[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 22 13:33:36 2025 +0900

    再ログインでtokenが取得できていない
    
    1回目はログインすると、2回目ではtoken消えている。

[33mcommit 7827b6f5a744f14b3bab454b8d8c99e7d757b63d[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 22 13:16:00 2025 +0900

    [UPDATE]ログインメアドでできた。
    
    k.okuma@ten-system.comでログイン処理OK
    だがtoken返らず

[33mcommit 68cd571df2b4313854188716e35dc65f883fffd1[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 22 10:20:46 2025 +0900

    [update]connの問題解決できた
    
    ChatGPTに3つのファイル見てもらった。main, init_module, __init__.
    するとconnectionエラーは治った。
    しかし　userid入力でエラーが発生しました
    no such table: User

[33mcommit 4738467d7532dada64d992e1bdcaa35f5b516b9e[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 21 11:54:36 2025 +0900

    checkを直した

[33mcommit a7acf59c9710c39a93ee63438b67a59eb23ab0b0[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 21 11:46:52 2025 +0900

    不要なコメントを消した

[33mcommit dbe369c19d8c30a2e801305515ac1e74feb1a5c5[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 21 11:13:28 2025 +0900

    tokenに期限を含めた

[33mcommit 07530d0b36704167f95f398ac229f51c25b77d78[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 21 10:00:49 2025 +0900

    apiフォルダ追加

[33mcommit f896d43926b4424ac74bc84b44b3eed67cf64f48[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Mon Jan 20 15:11:38 2025 +0900

    OpenAPI.yamlを追加して編集開始

[33mcommit 054088afb9e963951739ef66c0592eadd01c8e3f[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Mon Jan 20 13:26:33 2025 +0900

    とりあえずCookieは良しとなった

[33mcommit 36e4f1ccdf41c0bd8604746a4b595466264265d6[m
Merge: 332706e fefb3d4
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Jan 18 15:32:03 2025 +0900

    Merge branch 'main' of https://github.com/Kei-Okuma1216/Obento-Test

[33mcommit 332706ede23461e39e5256e0eac9dab02dfc8381[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Jan 18 15:29:42 2025 +0900

    秘密鍵をOpenSSLからjwtno

[33mcommit fefb3d4761248c896d87dcd29fdcd5fc088169ce[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Jan 18 15:09:09 2025 +0900

    Update README.md
    
    仮想環境の作成追加した

[33mcommit d57ff5cd39bd526175bf60b85aacd341471d1ae5[m
Merge: 5b78e71 3a864a5
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Jan 18 10:19:48 2025 +0900

    Merge branch 'main' of https://github.com/Kei-Okuma1216/Obento-Test

[33mcommit 5b78e71de8a66e0f6e96bf062437ca2bd2323228[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Jan 18 10:18:23 2025 +0900

    v_0.0.1フォルダ作成した

[33mcommit 3a864a5b71e4e350be4ac9105e52da3002d301f9[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Fri Jan 17 15:30:03 2025 +0900

    Update README.md
    
    127.0.0.1に直した

[33mcommit 499a3494554de0748aaf8ec5783204eddabb1f31[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Fri Jan 17 15:27:23 2025 +0900

    セキュリティの前まで終わった

[33mcommit 9282e42596718f6c0a0b6c4d18156b228a7c9183[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 16 15:22:45 2025 +0900

    VSCodeからpushした

[33mcommit 958273ae112a29e2852e3a3b55e15decc34f331b[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 15 15:14:29 2025 +0900

    チュートリアルでヘッダからCookie取得まで

[33mcommit 7db49014f9bd99b19ad088c4bf3fe14451de4ff3[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 15 11:28:05 2025 +0900

    privateモードで30秒で無効になった

[33mcommit a996f9e9763ea00dbb9729740a9868be00703d52[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 14 14:32:41 2025 +0900

    トークンがある場合は自動で/cdeに遷移できた

[33mcommit cf590069e7ad233bf15541831925ba4207b75442[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 14 13:47:29 2025 +0900

    Cookie保存解決済。２人に説明した。

[33mcommit 18043bd81b9c4a133686be3db5dab9cf5e1e5c5b[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Jan 11 15:01:18 2025 +0900

    secure=FalseにしたがCookieだめ

[33mcommit 4160f230053022e4bfb335391bbe2e3e6a8da6d5[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Jan 11 14:30:04 2025 +0900

    Cookieまだ入れず

[33mcommit 2856ce14e203bc1e2563b0c151e19e04ba5dba54[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Jan 11 14:01:24 2025 +0900

    Cookieha

[33mcommit 89647ec4b89a10892f9f44eea66b33887b585314[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Fri Jan 10 15:03:21 2025 +0900

    テンプレートのstyles.cssを取り消した。コンソールにエラーなし

[33mcommit 6de2a9f0dc75a6c2848325726ddf96f09ebc78b0[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Fri Jan 10 14:26:44 2025 +0900

    tokenの有効期限を30秒で試して動いた

[33mcommit e7bc93bcbcb24d22ef6b891ddec167b74cb1ddfc[m
Merge: 50b9dda 97a2193
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Fri Jan 10 13:48:48 2025 +0900

    Resolved merge conflictsMerge branch 'main' of https://github.com/Kei-Okuma1216/Obento-Test

[33mcommit 50b9dda4ba75dab8735cad0ebc59d3e9de509404[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Fri Jan 10 13:43:03 2025 +0900

    ローカルリポジトリをCドライブの直下に移動した

[33mcommit 97a2193435d8545aecfca1ca78d873f28a6e4f51[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 15:28:25 2025 +0900

    Update README.md

[33mcommit 05c02e548cff30aa50c1b89cbe411bbc36c258b4[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 15:26:40 2025 +0900

    Update README.md

[33mcommit f8ecd463192186da5e9806e4ef7652ca7a2da999[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 15:15:34 2025 +0900

    Update README.md

[33mcommit dd285f95f975a9efe5a482890794672b8e4e4cd9[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 15:13:35 2025 +0900

    Update README.md

[33mcommit 6bfd01124cb8b20e358a28f104ebb42f804675b7[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 14:48:38 2025 +0900

    Add FAQ folder and .3 md files

[33mcommit 49d0b7209a5919d5e2e60af5ea45255f6ade470e[m
Merge: 89e2e25 2227495
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 14:24:08 2025 +0900

    Resolved merge conflicts

[33mcommit 2227495f668caab3dec596659d47aeba23d3494d[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 14:19:05 2025 +0900

    Update .gitignore

[33mcommit 89e2e25825f8acc9a61fe54e42084c07144705b9[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 14:18:24 2025 +0900

    Add .env file

[33mcommit 1397d2593a072e7bdc54933aa065477d9c740257[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 14:13:54 2025 +0900

    Update .gitignore
    
    # .envにした

[33mcommit 40147fc10cdab7515b2be3043e6ecd4fe264554a[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 13:58:14 2025 +0900

    Create .gitignore

[33mcommit 861d3e7d4f5ae18804a0ca26692e542b3d8230c2[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 13:50:51 2025 +0900

    Rename file from old_filename.py to new_filename.py

[33mcommit 24e5790d1a85877ad87bde229db1746694710ae1[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 13:44:22 2025 +0900

    Rename file from old_filename.py to new_filename.py

[33mcommit 663c04862ee3649aba890f9ebeb53772b2f01622[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 13:34:59 2025 +0900

    Add folder and .py files

[33mcommit 1c324d4ba6d6fd508aafa7af2f6de0d56ebded34[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 13:04:17 2025 +0900

    JavaScriptのモジュール化をメモした

[33mcommit f5d86dd5358fe76710873cff995597d274edd96d[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Jan 9 11:16:53 2025 +0900

    トークンのエラー期限切れエラーは修正できた。日付も取り出せた

[33mcommit e72d8f1730319102809ae33e47881c7e1ae3ca1c[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 8 15:17:14 2025 +0900

    Update README.md
    
    OpenSSLのインストール追加

[33mcommit 489335d503ad31594934fc7a21a0b39e94dce75c[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 8 15:16:18 2025 +0900

    トークン別ページ渡すがエラーになるまで
    
    - OpenSSLのインストール
    - ```winget search openssl```
    - ```winget install ShiningLight.OpenSSL.Light```
    - ```openssl version```
    - ```winget list```
    - OpenSSLの場所表示する
       - ```dir /a /s c:\openssl.exe```

[33mcommit fb536d0930a741e935e6ed97c6633a0901b76576[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 8 15:11:40 2025 +0900

    abcにアクセスするとトークン期限切れエラーになる
    
    トークンが無効または期限切れです
    トークンを確認してください。

[33mcommit 871bdca8ddb51ff43b4a875326676315efdc81ff[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 8 11:41:03 2025 +0900

    random関数を削除した ローカル秘密鍵でアクセスに変更した
    
    random関数削除した
    cryptographyライブラリを導入して、OpenSSLの利用をやめた
    <ローカルファイルの扱い>
    HTTPS接続のuvicorn起動でmy-local.crtを使う
    プログラムで秘密鍵my-local.keyを使う

[33mcommit 748cd25dd247d01873689d9ee692c6de71614a38[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 8 10:08:06 2025 +0900

    Update README.md

[33mcommit 5690a7b1c9ebdb58acecb5e30b3a99cc01e07bd3[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Wed Jan 8 10:07:49 2025 +0900

    Update README.md
    
    チェックボックスの動作テスト

[33mcommit d41830ae4516358c323cdd646085ef03a51d96c9[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 7 15:13:49 2025 +0900

    1/7火曜時点のテスト可能な環境一式です

[33mcommit 73f7c6a3680521743df576edd44f0c6bcaca4e1a[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 7 15:00:01 2025 +0900

    Update README.md
    
    コードブロックをつけました

[33mcommit df9a5c5f1e74bb3ac7815f5b8486c6f233928b1f[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 7 14:57:49 2025 +0900

    Update README.md
    
    venvの簡易マニュアルを追加しました

[33mcommit 08b21bf66603083feb77bc78b0eee0856a29db1b[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 7 14:38:32 2025 +0900

    ユーザIDとパスワードを入力したら乱数を返すページにした

[33mcommit 6b91f1fe570ddee117a101f14681e7e6f96a1f05[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 7 14:21:44 2025 +0900

    /abcをつけると別のページを表示する

[33mcommit 88e0c9effe43285b5fb39aedb19185cbf6c5115a[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 7 13:30:49 2025 +0900

    簡単なユーザーページを表示した

[33mcommit 4c354ee8c75f2b77fc08cbca886d9a3cc76d07c5[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 7 13:21:50 2025 +0900

    localhostで単純な長文文字列返した

[33mcommit 9025d3878c70cda2f326a4a2043557c4fc968631[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 7 11:52:01 2025 +0900

    SSLブラウザアクセス自己署名証明書での実験できた

[33mcommit 3bc19101ea82ab65bf336ea1b667cba7908012d6[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Jan 7 10:50:33 2025 +0900

    hostsの記述削除しました

[33mcommit 19ef0f89c467ad5fecee5df624dd626090c6864b[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Mon Jan 6 15:21:21 2025 +0900

    OpenSSLで自己署名証明書が働かない
    
    1. FastAPI実装調査.md
    OpenSSLで自己署名証明書をつくる　より以降を追加しました。
    2. main.py
    FastAPIのプログラム。venvで起動後、localhostでアクセスできます。
    3. OpenSSLで実験.md
    参考資料です。Copilotに聞いたOpenSSLのやり方の質問結果です。（これもCtrl＋Shift＋Vでプレビューが開けます）

[33mcommit 5a434100ad8b7ba93eea3bc0a888a386dc77bd14[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Dec 28 15:26:39 2024 +0900

    OpenSSLインストールした直後
    
    まだJWT返却試していない
    https://atmarkit.itmedia.co.jp/ait/articles/1601/29/news043_2.html

[33mcommit 120c3fd8ef4724ca0ecf4e56ba91eb8b805be313[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Dec 28 15:25:13 2024 +0900

    レビュー２回目
    
    仕様変更有り
    自社カレンダー不要など

[33mcommit dac9580c4d4bdba9aff8cd3d99438ed79a17290a[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Dec 28 11:24:18 2024 +0900

    新規追加
    
    FastAPI実装調査.mdを新規追加しました。

[33mcommit 8183a1c8de793dd57b69c8e8d48139d014ebe40d[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Dec 28 11:23:20 2024 +0900

    JWT認証の説明を修正した

[33mcommit 7f8df42cd5096ce561c897e46e0fe1ae542b4d1e[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Sat Dec 28 10:13:44 2024 +0900

    JWT認証の開設追加しました。仕様書一旦締切。
    
    仕様書一旦締切

[33mcommit b6e402b50ebab4e4aea293c3bd383b016b144a75[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Fri Dec 27 15:19:29 2024 +0900

    Add files via upload
    
    ER図までできました。2024/12/28（土）レビュー準備のため更新。

[33mcommit 226d2a12ce0d71ff25cb551fcbf16b585c7c20b5[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Dec 26 15:13:01 2024 +0900

    ER図作成途中

[33mcommit eced1bc901b53c1fdb6f0a0ed135e8dc126fa4da[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Dec 26 13:39:22 2024 +0900

    シーケンス図に３つ目を追加しました

[33mcommit d17c90a521773876ab9db431e4f5bfe6594b67f7[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Thu Dec 26 13:09:31 2024 +0900

    設計書の最初のバックアップ
    
    設計書バックアップのため

[33mcommit b3dbe328e872bba18525d829f4c7abf1d9c96575[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Dec 24 10:45:03 2024 +0900

    サンプルのIndex.htmlファイルを追加した。

[33mcommit 6b970b65fe6befe64d5f3a482ce30fa1c2d67b59[m
Author: Kei Okuma <k.okuma@ten-system.com>
Date:   Tue Dec 24 10:44:18 2024 +0900

    Initial commit
