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
以下のファイルを\<SRCDIR\>に作成する。
- AWS へアップロードするファイルのシンボリックリンク
- 上記のリンク先をたどってデータ転送を行うスクリプトファイル upload.\<timestamp>.sh
- 転送元ファイルのチェックサムを記録する checksum.\<timestamp>.sh
### 転送されるデータ
**【eWES】**
<img src="https://github.com/user-attachments/assets/0aed04d1-e246-47c0-bce6-462e1aae4523" width="1000">
**【WTS】**
<img src="https://github.com/user-attachments/assets/0998fdfb-7f01-49b5-8aa2-853da20fc854" width="1000">

*転送されるデータが1つでも欠けている場合はシンボリックリンクのみ作成し、shファイルを作成せずに終了する。
### 実行例
```
singularity exec --disable-cache --bind /data1 $img python $SCRIPT upload --flowcellid <FLOWCELLID> --project_type {WTS,eWES} [--directory DIRECTORY] [--inclusion INCLUSION] [--exclusion EXCLUSION] [--srcdir SRCDIR]
```
| option           | 概要                       | default          |
|:-----------------|:--------------------------|:------------------|
|--flowcellid/-fc  |バッチ固有のID。OncoStationに掲載されている9桁の半角英数字 |None |
|--project_type/-t |解析種別。eWES/WTS          |None              |
|--directory/-d    |解析フォルダの親ディレクトリ |/data1/data/result |
|--exclusion/-e    |除外するSample IDを指定。カンマ区切りで複数指定可能 |None |
|--inclusion/-i    |アップロードするSample IDを指定。カンマ区切りで複数指定可能 |None |
|--srcdir/-s       |bashファイル等の出力ディレクトリパス |/data1/work/AWS/uploads |

**--exclusion と --inclusion は同時指定不可** \
実行後に以下の操作を行い、アップロードを完了する。
```
sh <srcdir>/upload.<timestamp>.sh
cd <srcdir> && qsub checksum.<timestamp>.sh
```

## 2\. ダウンロード
以下のファイルを\<SRCDIR\>に作成する。
- AWS からデータ転送を行うスクリプトファイル download.\<timestamp>.sh
### 転送されるデータ
**【eWES】**
<img src="https://github.com/user-attachments/assets/2cba53e4-9566-490d-b89f-8221f356d36a" width="1000">
**【WTS】**
<img src="https://github.com/user-attachments/assets/f00c6a9c-996e-4386-b1c5-3a76fd434ad8" width="1000">

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
sh download.<timestamp>.sh
```
⇒ \<srcdir>/info/\<timestamp>.tsv に AWS S3に格納されている当該検体データの情報を書き出す。\
&nbsp;&nbsp;&nbsp; *データはアーカイブされており、リストアする必要があるため長時間かかる。
