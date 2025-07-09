# 村山式トンネル安定性解析システム

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://classicaltunnelanalyzer.streamlit.app/)

トンネル切羽の安定性を改良版村山式を用いて評価するWebアプリケーションです。

## 🚀 主要機能

### 1. 直感的な入力インターフェース
- **トンネル諸元**: 切羽高さ、土被り、水圧
- **地山物性値**: 単位体積重量、粘着力、内部摩擦角
- **詳細設定**: 探索範囲、反復計算パラメータ

### 2. 高度な計算機能
- **改良版村山式アルゴリズム**: 対数らせんすべり面の厳密な幾何学的計算
- **上載荷重計算方法の選択**: 簡易法またはテルツァギーの土圧理論
- **収束計算の可視化**: リアルタイムプログレスバーと統計情報

### 3. 結果の可視化
- **P-x曲線**: 必要支保圧力の分布
- **収束履歴グラフ**: 反復計算の誤差推移
- **収束統計**: 各位置での収束性能

### 4. レポート機能
- **PDFレポート生成**: 計算結果の詳細レポート
- **安全性評価**: 3段階の判定基準

## 📋 必要要件

- Python 3.8以上
- 主要ライブラリ:
  - Streamlit 1.35.0+
  - NumPy 1.24.0+
  - SciPy 1.10.0+
  - Plotly 5.15.0+
  - Pydantic 2.0.0+
  - ReportLab 4.0.0+

## 🛠️ インストールと実行

### ローカル環境での実行

```bash
# リポジトリのクローン
git clone https://github.com/dobocreate/classical_tunnel_analyzer.git
cd classical_tunnel_analyzer

# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# アプリケーションの起動
streamlit run app.py
```

### Streamlit Cloudでの利用

以下のURLからアクセスできます：
https://classicaltunnelanalyzer.streamlit.app/

## 📊 計算理論

### 村山式の概要
村山式は、トンネル切羽前方に形成される対数らせんすべり面を仮定し、力の釣り合いから必要な支保圧力を算出する手法です。

### 改良点
1. **厳密な幾何学的計算**: SciPyのfsolveを用いた非線形方程式の解法
2. **テルツァギーの土圧理論**: アーチング効果を考慮した上載荷重計算
3. **収束性の向上**: 適応的な反復計算パラメータ

### 安全性評価基準
- **P < 50 kN/m²**: 切羽は安定（緑）
- **50 ≤ P < 100 kN/m²**: 軽微な支保が必要（黄）
- **P ≥ 100 kN/m²**: 強固な支保が必要（赤）

## 📁 プロジェクト構成

```
classical_tunnel_analyzer/
├── app.py                      # メインアプリケーション
├── src/
│   ├── murayama_new.py        # 改良版計算エンジン
│   ├── models.py              # データモデル定義
│   ├── convergence_utils.py   # 収束計算ユーティリティ
│   ├── report_generator.py    # レポート生成
│   └── murayama.py           # プリセット定義
├── docs/
│   ├── murayama_gemini.md    # アルゴリズム仕様書
│   └── テルツァギーの土圧理論.md
├── tests/                     # テストコード
├── requirements.txt           # 依存関係
├── claude.md                  # 開発履歴と技術仕様
└── README.md                  # このファイル
```

## 🧪 開発者向け情報

### テストの実行
```bash
pytest tests/
```

### コード品質チェック
```bash
# リンター
flake8 src/ --max-line-length=100

# 型チェック
mypy src/ --ignore-missing-imports

# フォーマッター
black src/ tests/
```

### 主要な設計判断
1. **Streamlitの採用**: 迅速なプロトタイピングと簡単なデプロイ
2. **Pydanticによるデータ検証**: 型安全性と入力検証の強化
3. **モジュラー設計**: 計算エンジンとUIの分離

## 🤝 貢献方法

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 📞 連絡先

問題や提案がある場合は、[Issues](https://github.com/dobocreate/classical_tunnel_analyzer/issues)で報告してください。

## 🙏 謝辞

- 村山式の理論的基礎を提供した研究者の方々
- Streamlitコミュニティのサポート
- オープンソースコントリビューター

---

最終更新: 2025年7月9日