# NVDA 日本語版 開発者メモ

NVDA日本語チーム 西本卓也


## ビルド環境準備とソースコード取得


NVDA 2017.4jp-beta の場合


### (1) Windows 10 64ビット

確実にビルドできる作業環境は Windows 10 64ビット (1703 / 1709)


### (2) Visual Studio 2017 Community

以下からダウンロードしてインストーラーを実行

https://www.visualstudio.com/ja/downloads/ 

2017年10月にリリースされた Visual Studio 2017 バージョン 15.4.0 を推奨。

#### (2.1) 選択する「ワークロード」の項目

(a) C++によるデスクトップ開発

(b) ユニバーサル Windows プラットフォーム開発

#### (2.2) 「概要」「C++によるデスクトップ開発」「オプション」で選択する項目

(a) VC++ 2017 v141 ツールセット（x86, x64）

(b) Windows 10 SDK (10.0.16299.0) for Desktop C++ x86 and x64


### (3) Git for Windows

Git for Windows サイトから Git-2.14.3-64-bit.exe をダウンロードする。

https://git-for-windows.github.io/

インストーラーを実行する。

Git の初心者は下記の設定を推奨。

* Adjusting your PATH environment : Use Git and optional Unix tools from the Windows Command Prompt

* Configuring the line ending conversions : Checkout as-is, commit as-is

その他はデフォルトで。

環境変数 PATH を自分で設定しなおす場合は、以下が登録されていること。

```
C:\Program Files\Git\cmd
C:\Program Files\Git\usr\bin
```

備考：
リモートリポジトリへのアップロード (git push) するためには
push 先（GitHubなど）のアカウントのセットアップや公開鍵の設定、権限の取得が必要。


### (4) 7-Zip (7z)

7-Zip サイトから 16.04 for Windows (7z1604-x64.exe) をダウンロードする。

http://www.7-zip.org/download.html

インストーラーを実行してデフォルトでインストールする。

環境変数 PATH に以下を登録する。

```
C:\Program Files\7-Zip
```

### (5) Python 3.6.3 / 2.7.14 (Windows 32bit)

それぞれダウンロードして両方実行し、インストールする。
オプションはデフォルトでよい。

https://www.python.org/downloads/release/python-363/

Windows x86 executable installer (python-3.6.3.exe)

https://www.python.org/downloads/release/python-2714/

Windows x86 MSI installer (python-2.7.14.msi)


### (6) 確認すること

コマンドプロンプトで

```
> py -2
```

を実行すると Python 2.7 が起動する。

コマンドプロンプトで git, patch, 7z がそれぞれ実行できる。


### (7) NVDAのソースコード取得


以下で本体および Git のサブモジュールが取得される。

日本語版のソースコード

```
> git clone --recursive https://github.com/nvdajp/nvdajp.git
```

本家版のソースコード

```
> git clone --recursive https://github.com/nvaccess/nvda.git
```

## ビルド


### Python 2 環境の有効化

以下を行うとカレントに py2env というフォルダが作成される。


```
> py -2 -m pip install virtualenv
> py -2 -m virtualenv py2env
> py2env\Scripts\activate
```

最後の activate を実行すると、ただ python と入力するだけで Python 2.7 が起動するようになる。


### 日本語版のビルド


py2env を activate して


```
(py2env) > cd nvdajp
(py2env) > jptools\nonCertAllBuild.cmd
```

詳細は後述（署名なしビルド）


### 本家版のビルド


```
(py2env) > cd nvda
(py2env) > python scons.py
```

scons.bat は拡張子 .py が Python 3 と関連付けされているとうまく動かない。


## git トラブルシューティング


### ファイルの不足やバージョンの不一致

サブモジュールの同期や更新の失敗。

下記を実行：

```
> git submodule sync
> git submodule update --init --recursive
```

備考：
本家から git fetch, git merge FETCH_HEAD したあとで

```
modified:   include/espeak (new commits)
```

のようになったときにこの操作をすると解決することが多い。

不必要な modified を誤ってマージして git push すると、
サブモジュールのバージョンが本家とずれた状態のまま GitHub に公開されてしまう。


### git submodule update のエラー対応

```
> git submodule update --init

fatal: reference is not a tree: 1e1e7587cfbc263b351644e52fdaf2684103d6c8
Unable to checkout '1e1e7587cfbc263b351644e52fdaf2684103d6c8' in submodule path 'include/liblouis'
```

include/liblouis サブモジュールの checkout に失敗している。

liblouis に cd して git fetch -t してからやり直してみる：

```
> cd include\liblouis
> git fetch -t

remote: Counting objects: 412, done.
remote: Compressing objects: 100% (144/144), done.
Remote: Total 412 (delta 268), reused 412 (delta 268)eceiving objects:  91% (37
Receiving objects: 100% (412/412), 86.54 KiB | 0 bytes/s, done.
（略）

> cd ..\..
> git submodule update --init --recursive
```

## 署名なしビルド

署名なしビルドは、最上位のディレクトリで以下を実行

```
jptools\nonCertAllBuild.cmd
```

出力は output フォルダに作られる。
実行した日付のついた nvda_20**.*jp-beta-YYMMDDx.exe というファイル名になる。

AppVeyor 署名なしビルドのプロジェクト nvdajp-noncert

https://ci.appveyor.com/project/TakuyaNishimoto/nvdajp-q4r95

Custom configuration .yml file name に appveyor-jp-noncert.yml を指定している。

作業記録:
https://osdn.net/ticket/browse.php?group_id=4221&tid=36665


## 署名つきビルド

署名つきビルドは、必要なファイルを追加して、最上位のディレクトリで以下を実行

```
jptools\kcCertAllBuild.cmd
```

## AppVeyor


### AppVeyor プロジェクト設定

nvdajp は以下のように設定している

https://ci.appveyor.com/project/TakuyaNishimoto/nvdajp/settings


```
[General]

GitHub repository:
nvdajp/nvdajp

Default branch:
jpbeta

Custom configulation .yml file name:
appveyor-jp.yml


[Environment]

Build worker image:
Visual Studio 2017
```


### appveyor-jp.yml の内容

本家の appveyor.yml をそのまま使わず、
前述の jptools\kcCertAllBuild.cmd を呼び出している。


各種エラー回避の記録：

https://osdn.jp/ticket/browse.php?group_id=4221&tid=36010


本家版 NVDA を AppVeyor でビルドするために
コードサイニング証明書を暗号化している。
日本語版は独自のコードサイニング証明書を追加している。

この暗号化は AppVeyor アカウントと紐付いており、
他のユーザーが AppVeyor でビルドすると、
コードサイニングに失敗するはずである。


### AppVeyor でのファイル暗号化

http://www.appveyor.com/docs/how-to/secure-files

解説記事（チケット）とその引用：

https://osdn.jp/ticket/browse.php?group_id=4221&tid=36180

なぜ暗号化されたファイルと、その暗号化を解くための秘密文字列を
両方公開して大丈夫なのか、
理屈がわかりにくいが、こういうことになっている：

* PFX ファイル(A)（秘密にしたいファイル）
* ユーザーが設定した秘密文字列(B)
* PFX ファイル(A) を秘密文字列(B) で暗号化したファイル(C)
* 秘密文字列(B) を AppVeyor が暗号化した文字列(D) （ユーザーには見えないがここで AppVeyor が秘密文字列 (E) を使用） 

公開される情報

* (C) 暗号化された PFX ファイル
* (D) 暗号化された秘密文字列 

公開されない情報

* (A), (B) : ユーザーが秘密にしたい情報
* (E) : AppVeyor が秘密にしている情報 

(E) がないので (C), (D) から (A), (B) を得ることができない。

（以上）
