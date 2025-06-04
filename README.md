# aws
AWS (Amazon Web Service) に解析データをアップロード、またはダウンロードする。\
計算ノードはawsコマンドがインストールされていないため、作成されたbashスクリプトはqmasterで実行すること。\
(長時間かかるので、nohupでバックグラウンド実行を推奨)

## 変数の定義(共通)
```
img=/data1/labTools/labTools.sif
SCRIPT=/data1/labTools/aws/latest/aws.py
```
マニュアルの表示（全体）
```
$ singularity exec --disable-cache --bind /data1 $img python $SCRIPT --help
version: v3.0.0
usage: aws.py [-h] [--version] {upload,up,download,dl} ...

Backup analysis data to AWS.

positional arguments:
  {upload,up,download,dl}
    upload (up)         Upload to AWS.
    download (dl)       Download from AWS.

optional arguments:
  -h, --help            show this help message and exit
  --version, -v         show program's version number and exit
```
コマンド別の詳細表示
```
singularity exec --disable-cache --bind /data1 $img python $SCRIPT <command> --help
```
## 1\. アップロード
以下のファイルを作成する。
- AWS へアップロードするファイルのシンボリックリンク
- 上記のリンク先をたどってデータ転送を行うスクリプトファイル upload.\<time-stamp>.sh
- 転送元ファイルのチェックサムを記録する checksum.\<time-stamp>.sh
### 実行例
```
singularity exec --disable-cache --bind /data1 $img python $SCRIPT upload --flowcellid <FLOWCELLID> --project_type {WTS,eWES} [--directory DIRECTORY] [--inclusion INCLUSION] [--exclusion EXCLUSION] [--srcdir SRCDIR]
```
| option           | 概要                       | default          |
|:-----------------|:--------------------------|:------------------|
|--flowcellid/-fc  |バッチ固有のID。OncoStationに掲載されている9桁の半角英数字 |None |
|--project_type/-t |解析種別。eWES/WTS          |None              |
|--directory/-d    |解析フォルダの親ディレクトリ |/data1/data/result |
|--exclusion/-e    |アップロードするSample IDを指定。カンマ区切りで複数指定可能 |None |
|--inclusion/-i    |除外するSample IDを指定。カンマ区切りで複数指定可能 |None |
|--srcdir/-s       |bashファイル等の出力ディレクトリパス |/data1/work/AWS/uploads |

実行後に以下の操作を行い、アップロードを完了する。
```
sh <srcdir>/upload.<time-stamp>.sh
cd <srcdir> && qsub checksum.<time-stamp>.sh
```

## 2\. ダウンロード
以下のファイルを作成する。
- AWS からデータ転送を行うスクリプトファイル download.\<time-stamp>.sh
### 実行例
```
singularity exec --disable-cache --bind /data1 $img python $SCRIPT download --sample SAMPLE [--srcdir SRCDIR]
```
| option     | 概要                               | default          |
|:-----------|:----------------------------------|:------------------|
|--sample/-s |Sample ID。カンマ区切りで複数指定可能 |None |
|--srcdir/-d |bashファイル等の出力ディレクトリパス  |/data1/work/AWS/downloads |

実行後に以下の操作を行い、ダウンロードを完了する。
```
sh download.<time-stamp>.sh
```
⇒ \<srcdir>/info/\<time-stamp>.tsv に AWS S3に格納されている当該検体データの情報を書き出す。\
&nbsp;&nbsp;&nbsp; *データはアーカイブされており、リストアする必要があるため長時間かかる。
