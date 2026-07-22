[English version](README.md)

# dd_draw — 低分子化合物リストをソート可能・プロパティ表示付きのグリッドとしてレイアウト

低分子化合物のリスト（`.smi` または `.sdf`）を受け取り、各分子を2D構造式として描画し、
化合物名と選択したプロパティを添えてグリッド状に並べ、自己完結型HTMLページまたは
ページ分割されたPDFとして出力する。それだけのツール — dd_drawは分子の標準化・
フィルタリング・ドッキングなどは一切行わない。それらは他の`dd_*`プロジェクト
（[dd_prep](https://github.com/rhara/dd_prep)、
[dd_chembl](https://github.com/rhara/dd_chembl) など）がすでに担っており、
dd_drawは「この化合物群を見る」という最後の一手のみを担当する。

## 概要

- **入力**: `.smi`/`.smiles`（1行ごとに空白区切りの `SMILES [名前]`）または
  `.sdf`/`.sd`/`.mol`（全てのSDタグが自動的にプロパティになる。追加オプション不要）
- **出力**: 自己完結型HTML（各構造式はインライン`<svg>`、CDN不要・外部ファイル不要 —
  オフラインで開ける、1ファイルとしてメール/Slackで送れる）またはページ分割されたPDF
  （出力パスの拡張子で自動判定）
- **プロパティ**: 利用可能なプロパティのうち任意の部分集合を各化合物に表示
  （`--props`）。指定しなければ見つかった全プロパティの和集合を表示する。
  `.smi`入力は本来プロパティを持たないため、`--compute-props`でRDKit記述子
  （MW, LogP, TPSA, HBD, HBA, RotB, NumRings, HeavyAtoms, FractionCSP3, QED）を
  その場で計算して付与でき、`--props-csv`で化合物名をキーとした外部テーブルを
  マージすることもできる
- **ソート**: `--sort-by NAME`でグリッド全体を任意の1プロパティで昇順/降順
  （`--descending`）に並べ替える。そのプロパティを持たない化合物は方向に関わらず
  常に末尾に配置される
- **向き**: 既定では全ての構造式をできるだけ横長になるよう回転する
  （`--no-orient-horizontal`で各分子の元の向きのまま保持することも可能）——
  2D構造式生成（その場で計算したものでも、入力ファイルに既に含まれていたもの
  でも）は縦長のレイアウトになることがあり、横長のグリッドセルの大半が
  無駄になってしまうため
- **原子・結合インデクス**: `--atom-indices`/`--bond-indices`で各原子・結合に
  RDKitのインデクスを添えて表示できる（ドッキング/SAR所見の報告や、SMARTS
  アンカーの指定など、特定の原子・結合を参照したい場合に）
- **Jupyter API**: `MoleculeGrid`はCLI・HTMLレンダラー・PDFレンダラーが共有する
  唯一のオブジェクト — 構築して`sort_by(...)`（メソッドチェーン可）し、
  そのままノートブック上にインライン表示（`_repr_html_`）するか、
  ファイルに書き出す（`to_html`/`to_pdf`）

## 構成

```
data/
  build_sample_drugs.py  下記サンプルデータの再生成スクリプト
  sample_drugs.smi       著名な承認薬29種、SMILESと名前のみ
  sample_drugs.sdf       同じ29種に MW/LogP/TPSA/HBD/HBA/RotB/QED/Score をSDタグとして付与

dd_draw/                    再利用可能なパッケージ本体
  io_utils.py             Record、read_smi / read_sdf / load_molecules、
                           compute_descriptors（RDKit記述子レジストリ）、
                           merge_properties_csv
  depict.py                mol_to_svg - Mol1つ → サイズ指定付きSVG1つ、両レンダラーが共有
  layout.py                MoleculeGrid - レコード + 表示/ソート/レイアウト設定。
                           from_smiles / from_sdf / from_file、sort_by、to_html、to_pdf
  render_html.py           render_html - 自己完結型HTML（jinja2 + インラインSVG）
  render_pdf.py            render_pdf - ページ分割PDF（reportlab + svglib、純Python）
  templates/grid.html      HTMLグリッドのjinja2テンプレート
  cli.py                   CLI引数解析（コンソールスクリプト: dd_draw）

tests/                     上記各モジュールを網羅するpytestスイート
```

## インストール

dd_drawは他の`dd_*`プロジェクトとは独立した専用環境（このスイート全体の慣習通り）
— 名前 `dd_draw`、Python 3.12 — を持つ。純PythonとRDKitのみで構成され、
C++コンパイラ・システムのCairo/Pango/GTKなどは不要、プラットフォーム固有コードも
一切無いため、Linux・macOS・Windowsで全く同じ手順でビルド・実行できる。

パッケージ管理はmamba(/conda)優先: 実質的な依存関係は全てconda-forgeから導入する。
`pip`はdd_draw自体の編集可能インストールにのみ使用し、常に`--no-deps`を付ける
（conda-forgeで入れた依存関係をpipが上書きしないように）。

**Linux / macOS / Windows（全く同じコマンド）:**

```bash
mamba create -n dd_draw -c conda-forge python=3.12 rdkit numpy jinja2 reportlab svglib pytest
mamba activate dd_draw
cd dd_draw
pip install --no-deps -e .   # dd_draw自体の編集可能インストール。固定インストールなら -e を外す
```

（mambaが無い場合は`conda`でも全く同様に動作する。）

**mamba/condaが使えない場合（どのプラットフォームでも）:** RDKit・numpy・
jinja2・reportlab・svglibは全て通常のPyPIホイールとしても配布されているため、
素のvenvでも動作する:

```bash
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

インストール後は、どのディレクトリからでも `import dd_draw` と `dd_draw` コマンドが使える。

### PDF出力にreportlab+svglibを使う理由（WeasyPrint/cairosvgではなく）

HTML/CSSのグリッドをそのままPDFに変換する（WeasyPrintなど）方がコード量は
少なく済んだはずだが、WeasyPrintもcairosvgもシステムのCairo/Pango/GDK-pixbuf
ライブラリを必要とする — Linux/macOSではconda-forge経由で問題なく入るが、
Windowsでは別途GTK3ランタイムのインストールが必要になるという既知の落とし穴が
ある。`reportlab` + `svglib`は純Python（svglibの非Python依存は`lxml`のみで、
どの環境でもビルド済みホイールが配布されている）なので、`mamba create`だけで
3プラットフォームとも全く同じPDF生成挙動になる。トレードオフとして、
`render_pdf.py`は`render_html.py`のCSSグリッドを再利用せず、各分子のSVGから
独自にグリッドをレイアウトしている（プレーンPDFにはCSSグリッドに相当する
共有可能な仕組みが無いため）。

### 横向きへの自動回転

RDKitの2D座標生成は「妥当な（重なりの無い）レイアウトのどれか1つ」を選ぶ
だけで、必ずしも横長になるとは限らない——さらに、他のツールが書いた
SDFから読み込んだ分子は、そのファイル自身の座標がもともとどんな向きで
あろうと、それをそのまま引き継ぐ。既定では、`depict.py`が各分子の原子
座標にPCA（主成分分析）を適用し、最も広がっている軸が水平になるよう
回転する（それでもなお縦長になる場合は直交する軸にフォールバックする——
十字型のレイアウトなど、分散最大の軸がバウンディングボックス上最も広い
軸と一致しないケース向け）。`--no-orient-horizontal`
（APIでは`orient_horizontal=False`）を指定すると、分子本来の向きを
そのまま保持する——入力座標自体に意味がある場合（例: ポケット内での
ドッキングポーズの向きを再現したい場合など）に有用。

## 使い方

```bash
# HTML: 自己完結型、オフラインでどのブラウザでも開ける
dd_draw data/sample_drugs.sdf -o grid.html --props MW,LogP,TPSA,Score --sort-by Score --descending --cols 5

# PDF: 同じグリッドをページ分割
dd_draw data/sample_drugs.sdf -o grid.pdf --props MW,LogP --sort-by MW --cols 4

# .smiは本来プロパティを持たない -- その場でRDKit記述子を計算
dd_draw data/sample_drugs.smi -o grid.html --compute-props MW,LogP,TPSA --sort-by MW

# 自前のプロパティテーブルをマージ（化合物名をキーとするCSV、既定では先頭列がキー）
dd_draw hits.smi -o hits.html --props-csv docking_scores.csv --sort-by docking_score

# 原子・結合インデクスを表示、かつ各分子の元の向きを保持（自動回転しない）
dd_draw hits.sdf -o hits.html --atom-indices --bond-indices --no-orient-horizontal
```

全オプション一覧: `dd_draw --help`

| オプション | 説明 | 既定値 |
|---|---|---|
| `-o`/`--output` | 出力パス。拡張子（`.html`/`.htm` または `.pdf`）で形式を判定 | 必須 |
| `--props` | 表示するプロパティ名（カンマ区切り） | 入力全体で見つかった全プロパティ |
| `--compute-props` | 計算して付与するRDKit記述子（カンマ区切り、`all`で全部） | なし |
| `--props-csv` | 化合物名をキーとしてマージする外部CSV | なし |
| `--props-csv-key` | `--props-csv`のキー列名 | CSVの先頭列 |
| `--sort-by` | ソート対象のプロパティ名。値が無い化合物は常に末尾 | 入力順 |
| `--descending` | `--sort-by`を降順にする（既定は昇順） | 昇順 |
| `--cols` | 1行あたりの分子数 | 4 |
| `--cell-width` / `--cell-height` | 構造式描画サイズ（ピクセル） | 250 / 200 |
| `--title` | ページ/文書タイトル | なし |
| `--no-orient-horizontal` | 各分子の元の2D向きを保持し、横長への自動回転を行わない | 回転する |
| `--atom-indices` | 各原子にRDKitの原子インデクスを表示 | オフ |
| `--bond-indices` | 各結合にRDKitの結合インデクスを表示 | オフ |

`--compute-props`で使える記述子: `MW`, `LogP`, `TPSA`, `HBD`, `HBA`, `RotB`,
`NumRings`, `HeavyAtoms`, `FractionCSP3`, `QED`。

### Python / Jupyter API

```python
from dd_draw import MoleculeGrid

# SDF: SDタグが自動的にプロパティになる
grid = MoleculeGrid.from_sdf("data/sample_drugs.sdf", properties=["MW", "LogP", "Score"])
grid.sort_by("Score", ascending=False)
grid  # ノートブックセルの最後の式として評価すると、そのままグリッドがインライン表示される

grid.to_html("hits_grid.html")
grid.to_pdf("hits_grid.pdf")

# SMILES: 本来プロパティを持たないため、計算またはマージで付与する
grid2 = MoleculeGrid.from_smiles(
    "data/sample_drugs.smi",
    compute_props=["MW", "LogP", "TPSA"],
    mols_per_row=5,
    title="My library",
).sort_by("MW")

# 原子・結合インデクスを表示、元の向きを保持（自動回転しない）
grid3 = MoleculeGrid.from_sdf(
    "hits.sdf",
    atom_indices=True,
    bond_indices=True,
    orient_horizontal=False,
)
```

`MoleculeGrid.from_file(path, ...)`はCLIと同様、拡張子で
`from_smiles`/`from_sdf`に自動振り分けする。

## サンプルデータ

`data/sample_drugs.smi`/`.sdf`: 著名な承認薬29種（アスピリン、カフェイン、
イブプロフェン、メトホルミン、プロプラノロール、フルオキセチンなど）。
広さよりも構造の単純さ・検証しやすさを優先して選定した。全SMILESがRDKitで
パース可能であり、重複構造は無く、コミット前に全ての分子式・分子量を
既知の文献値と突き合わせて確認済み。`.sdf`にはさらにMW/LogP/TPSA/HBD/HBA/RotB/QED
と、デモのソート対象として使える合成的な`Score`（`QED * 100`）をSDタグとして
付与している。`python data/build_sample_drugs.py`（`dd_draw`環境を有効化した状態）
で再生成できる。

## 依存関係

RDKit >= 2024.09.2（2D構造式描画）、numpy（横向き自動回転のPCA計算）、
Jinja2 >= 3.1（HTMLテンプレート）、reportlab >= 4.0 + svglib >= 1.5
（PDF生成）。JavaScript・CDN・システムのCairo/Pango/GTKは一切不要。

## ライセンス

MIT — [LICENSE](LICENSE) を参照。
