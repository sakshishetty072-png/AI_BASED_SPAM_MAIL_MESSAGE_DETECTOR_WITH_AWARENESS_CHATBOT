import os
import glob
import argparse
import pickle
import pandas as pd
import sys
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# ensure project root (one level up) is on sys.path so imports like `from text_utils import clean_text`
# work when running the script from the models/ directory
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from text_utils import clean_text

MODEL_OUT = os.path.join("models_downloaded", "random_forest_model.pkl")
VECT_OUT = os.path.join("models_downloaded", "vectorizer_rf.pkl")


def find_dataset(provided_path=None):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    candidates = []
    if provided_path:
        candidates.append(provided_path)
    candidates += [
        os.path.join(project_root, "dataset", "spam_ham_dataset.csv"),
        os.path.join(project_root, "dataset", "spam.csv"),
        os.path.join(project_root, "spam_ham_dataset.csv"),
        os.path.join(project_root, "spam.csv"),
    ]
    # add any CSVs inside dataset/ as fallbacks
    candidates += glob.glob(os.path.join(project_root, "dataset", "*.csv"))
    for p in candidates:
        if p and os.path.exists(p):
            return os.path.abspath(p)
    raise FileNotFoundError(
        "Dataset not found. Searched paths:\n" + "\n".join(candidates) +
        "\n\nPlace your CSV in ./dataset/ (spam_ham_dataset.csv) or pass --data <path>."
    )


def load_dataset(path):
    df = pd.read_csv(path)
    # detect common column names
    if "text" in df.columns and "label" in df.columns:
        text_col, label_col = "text", "label"
    elif "message" in df.columns and "label" in df.columns:
        text_col, label_col = "message", "label"
    elif "v2" in df.columns and "v1" in df.columns:  # common Kaggle naming
        text_col, label_col = "v2", "v1"
    else:
        cols = list(df.columns)
        if len(cols) < 2:
            raise ValueError("Dataset must contain at least two columns (label and text).")
        label_col, text_col = cols[0], cols[1]

    df = df[[text_col, label_col]].dropna()
    df[label_col] = df[label_col].astype(str).str.lower()
    df["label_num"] = df[label_col].map({"ham": 0, "spam": 1})
    if df["label_num"].isnull().any():
        # try coercing numeric labels
        df["label_num"] = pd.to_numeric(df[label_col], errors="coerce").fillna(df["label_num"])
        df["label_num"] = df["label_num"].astype(int)
    df["clean_text"] = df[text_col].astype(str).apply(clean_text)
    return df[["clean_text", "label_num"]]


def train_and_save(data_path, test_size=0.2, random_state=42, n_estimators=200):
    df = load_dataset(data_path)
    X = df["clean_text"]
    y = df["label_num"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    vect = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
    X_train_vec = vect.fit_transform(X_train)
    X_test_vec = vect.transform(X_test)

    clf = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state, n_jobs=-1)
    clf.fit(X_train_vec, y_train)

    y_pred = clf.predict(X_test_vec)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=["ham", "spam"])

    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    with open(MODEL_OUT, "wb") as f:
        pickle.dump(clf, f)
    with open(VECT_OUT, "wb") as f:
        pickle.dump(vect, f)

    print(f"Model saved: {os.path.abspath(MODEL_OUT)}")
    print(f"Vectorizer saved: {os.path.abspath(VECT_OUT)}")
    print(f"Accuracy: {acc:.4f}")
    print("Classification report:")
    print(report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train RandomForest spam detector")
    parser.add_argument("--data", "-d", help="Path to CSV dataset")
    args = parser.parse_args()
    dataset_path = find_dataset(args.data)
    print("Using dataset:", dataset_path)
    train_and_save(dataset_path) 
