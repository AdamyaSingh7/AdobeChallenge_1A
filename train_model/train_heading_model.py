import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

# Sample synthetic data (font_size, is_bold, y_pct, text_length, label)
data = [
    [20, 1, 0.05, 10, "Title"],
    [18, 1, 0.10, 15, "H1"],
    [16, 1, 0.15, 18, "H2"],
    [14, 0, 0.20, 30, "H3"],
    [12, 0, 0.30, 60, "Body"],
    [11, 0, 0.90, 80, "Footer"],
]

df = pd.DataFrame(data, columns=["font_size", "is_bold", "y_pct", "text_length", "label"])
df["label_num"] = df["label"].map({"Title": 0, "H1": 1, "H2": 2, "H3": 3, "Body": 4, "Footer": 5})

X = df[["font_size", "is_bold", "y_pct", "text_length"]]
y = df["label_num"]

model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
model.fit(X, y)

os.makedirs("../models", exist_ok=True)
joblib.dump(model, "../models/heading_classifier.pkl")

print("✅ Model trained and saved to /models/heading_classifier.pkl")
