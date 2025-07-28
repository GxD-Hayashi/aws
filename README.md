# aws
AWS (Amazon Web Service) に解析データをアップロード、またはダウンロードする。\
指定されたsample IDやflowcell IDから検体情報をデータベースに問合せ、CAPサーバ内のファイルを検索して転送するため、データベースに登録がない検体や、規程の場所にファイルがない検体に対しては実行できません。\
**また、データベースの設計内容が不明なため、データベース検索時に想定外の動作を行う可能性があります。**\
なお、計算ノードはawsコマンドがインストールされていないため、awsアップロード/ダウンロード用bashスクリプトはqmasterで実行してください。(長時間かかるので、nohupでバックグラウンド実行を推奨)

## エイリアスの作成 ※ 初回のみ
~/bin フォルダ直下に以下のコマンドを記載したテキストファイル aws_tools を作成し、実行権限を付与する。※ awsコマンドが既にあるので、エイリアス名はaws_toolsとする \
（gxd_pipeline, guest_user ユーザーには実装済み）\
エイリアスを作成しない場合は、singularity でコンテナとスクリプトファイルを指定して実行する。 
```
singularity exec --disable-cache --bind /data1 /data1/labTools/labTools.sif python /data1/labTools/aws/latest/aws.py $@
```
helpページを表示してエイリアスの設定を確認する。以下が表示されればOK。
```
$ aws_tools --help
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
aws_tools <command> --help
```
## 1\. アップロード
```
aws_tools upload --flowcellid <flowcellid>
aws_tools up -fc <flowcellid>
```
⇒ 以下のファイルが\<SRCDIR\>に作成される。
- AWS へアップロードするファイルのシンボリックリンク
- 上記のリンク先をたどってデータ転送を行うスクリプトファイル upload.\<timestamp>.sh
- 転送元ファイルのチェックサムを記録する checksum.\<timestamp>.sh
### 転送されるデータ
**【eWES】**
<img src="https://github.com/user-attachments/assets/0aed04d1-e246-47c0-bce6-462e1aae4523" width="1000">
**【WTS】**
<img src="https://github.com/user-attachments/assets/0998fdfb-7f01-49b5-8aa2-853da20fc854" width="1000">

※ 転送されるデータが1つでも欠けている場合は、存在しているデータのシンボリックリンクを作成し、bashファイルを作成せずに終了する。\
upload.\<timestamp>.sh, checksum.\<timestamp>.sh が作成されなかった場合は、足りないシンボリックリンクから欠けているデータを確認して対応する。
| option           |required| 概要                       | default          |
|:-----------------|:-------|:--------------------------|:------------------|
|--flowcellid/-fc  |True    |バッチ固有のID。OncoStationに掲載されている9桁の半角英数字 |None |
|--project_type/-t |False   |解析種別。both/eWES/WTSから選択 |both            |
|--directory/-d    |False   |解析フォルダの親ディレクトリ |/data1/data/result  |
|--exclusion/-e    |False   |除外するSample IDを指定。カンマ区切りで複数指定可能 |None |
|--inclusion/-i    |False   |アップロードするSample IDを指定。カンマ区切りで複数指定可能 |None |
|--srcdir/-s       |False   |bashファイル等の出力ディレクトリパス |/data1/work/AWS/uploads |

**※ --exclusion と --inclusion は同時指定不可** \
実行後に以下の操作を行い、アップロードを完了する。
```
sh <srcdir>/upload.<timestamp>.sh
cd <srcdir> && qsub checksum.<timestamp>.sh
```

## 2\. ダウンロード
```
aws_tools download --sample <samples>
aws_tools dl -s <samples>
```
または
```
aws_tools download --listfile <sample IDs listfile path>
aws_tools dl -f <sample IDs listfile path>
```
⇒ 以下のファイルが\<SRCDIR\>に作成される。
- AWS からデータ転送を行うスクリプトファイル download.\<timestamp>.sh
### 転送されるデータ
**【eWES】**
<img src="https://github.com/user-attachments/assets/2cba53e4-9566-490d-b89f-8221f356d36a" width="1000">
**【WTS】**
<img src="https://github.com/user-attachments/assets/f00c6a9c-996e-4386-b1c5-3a76fd434ad8" width="1000">
| option       |required| 概要                               | default           |
|:-------------|:-------|:-----------------------------------|:------------------|
|--sample/-s   |False*  |Sample ID。カンマ区切りで複数指定可能 |None               |
|--listfile/-f |False*  |downloadするSample IDリストのファイルパス。<br>Sample IDを1列に記載する |None |
|--srcdir/-d   |False   |bashファイル等の出力ディレクトリパス  |/data1/work/AWS/downloads |

**※ --sample または --listfile のいずれか1つを指定する。** 検査種別は混合していても問題ありません。\
実行後に以下の操作を行い、ダウンロードを完了する。
```
sh download.<timestamp>.sh
```
⇒ \<srcdir>/info/\<timestamp>.tsv に AWS S3に格納されている指定した検体データの情報を書き出す。\
&nbsp;&nbsp;&nbsp; ※ データはアーカイブされており、リストアする必要があるため長時間かかる。
