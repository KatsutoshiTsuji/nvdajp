NVDA 日本語版 開発者メモ

NVDA日本語チーム 西本卓也


1. ビルド環境


NVDA 2015.3jp の場合


(1) Windows 7 SP1 32ビットまたは64ビット

備考：Windows 8.1 でビルドして 7 にインストールするとエラーが出る問題
https://sourceforge.jp/ticket/browse.php?group_id=4221&tid=34057


(2) Visual Studio 2012 Express for Desktop (Update 4)

(3) Visual Studio 2015 Express for Desktop

備考：
VS2012 は NVDA コアのコンパイルに必要、VS2015 は JTalk のコンパイルで使用。
Express ではなく Pro や Ultimate でもよい。


(4) git (msysgit 1.9.2)

備考：
git push するためには push 先のアカウントのセットアップや公開鍵の設定、
権限の取得が必要。


(5) 7z (C:\Program Files (x86)\7-Zip\7z.exe に PATH が通っていること）

miscDepsJp から sources へのコピーで使用している。


(6) Python 2.7.10 (Windows 32bit)

C:\Python27\python.exe に PATH が通っていること。


2. サブモジュールの取得

> git submodule sync
> git submodule update --init --recursive

備考：
本家から git fetch, git merge FETCH_HEAD したあとで

        modified:   include/espeak (new commits)

のようになったときにこの操作をすると解決することが多い。


2.1 git submodule のエラー対応

> git submodule update --init

fatal: reference is not a tree: 1e1e7587cfbc263b351644e52fdaf2684103d6c8
Unable to checkout '1e1e7587cfbc263b351644e52fdaf2684103d6c8' in submodule path
'include/liblouis'

include/liblouis サブモジュールの checkout に失敗している。
liblouis に cd して git fetch -t してからやり直してみる：

> cd include\liblouis
> git fetch -t

remote: Counting objects: 412, done.
remote: Compressing objects: 100% (144/144), done.
Remote: Total 412 (delta 268), reused 412 (delta 268)eceiving objects:  91% (37
Receiving objects: 100% (412/412), 86.54 KiB | 0 bytes/s, done.
（略）

> cd ..\..
> git submodule update --init --recursive


3. 署名つきビルド

署名つきビルドは、最上位のディレクトリで以下を実行

jptools\kcCertAllBuild.cmd

または

(1) scons -c
(2) jptools\setupMiscDepsJp.cmd
(3) jptools\kcCertMiscDepsJp.cmd
(4) jptools\kcCertBuild.cmd

補足:
(2) は JTalk と日本語点訳エンジンを更新する。
(3) は libopenjtalk, libmecab, directbm の各DLLを署名する。
(3) で署名ツールがエラーを出したらやり直す。


4. 署名なしビルド

署名なしビルドは、最上位のディレクトリで以下を実行

jptools\nonCertAllBuild.cmd

または

(1) jptools\setupMiscDepsJp.cmd
(2) jptools\nonCertBuild.cmd
JTalk または日本語点訳エンジンを更新しない場合は (1) は不要。

出力は output フォルダに作られる。
実行した日付のついた nvda_20**.*jp-beta-YYMMDD.exe というファイル名になる。


5. その他の作業用スクリプト


5.1 事前に不要ファイルの確認

jptools\findBackupFiles.cmd

必要に応じて削除。

内部で gnupack の find.exe を使っている。


5.2 レポジトリにプッシュ

jptools\push_remote.cmd

git remote -v の状況：

origin     git@github.com:nvdajp/nvdajp.git (fetch)
origin     git@github.com:nvdajp/nvdajp.git (push)
nvaccess   git://git.nvaccess.org/nvda.git (fetch)
nvaccess   git://git.nvaccess.org/nvda.git (push)


5.3 clean miscdep

jptools\clean_miscdep.cmd


5.5 2014.3jp までの署名つきリリースの手順

http://ja.nishimotz.com/nvdajp_certfile
