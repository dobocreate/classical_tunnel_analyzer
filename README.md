# Murayama Tunnel Stability Evaluation App

トンネル切羽の安定性を村山の式を用いて評価するStreamlitアプリケーション

## 主要機能
- トンネル形状と地山パラメータの入力
- P-B曲線（抵抗力-すべり幅曲線）の計算
- 最大抵抗力と安全率の算出
- 結果の可視化とレポート出力

## 使用方法
```bash
# 依存関係のインストール
pip install -r requirements.txt

# アプリケーションの起動
streamlit run app.py
```

## 技術スタック
- Python 3.11+
- Streamlit
- NumPy, Pandas
- Plotly
- Pydantic