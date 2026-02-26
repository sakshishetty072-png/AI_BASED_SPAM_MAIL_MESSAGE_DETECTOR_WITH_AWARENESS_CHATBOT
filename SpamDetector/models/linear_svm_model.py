import os
import glob
import argparse
import pickle
import sys
import pandas as pd

# ensure project root (one level up) is on sys.path so imports like `from text_utils import clean_text` work
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from text_utils import clean_text

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, classification_report

MODEL_OUT = os.path.join("models_downloaded", "linear_svm_model.pkl")
VECT_OUT = os.path.join("models_downloaded", "vectorizer_svm.pkl")


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
    elif "v2" in df.columns and "v1" in df.columns:  # kaggle spam dataset naming
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
        df["label_num"] = pd.to_numeric(df[label_col], errors="coerce").fillna(df["label_num"])
        df["label_num"] = df["label_num"].astype(int)

    df["clean_text"] = df[text_col].astype(str).apply(clean_text)
    return df[["clean_text", "label_num"]]


def train_and_save(data_path, test_size=0.2, random_state=42, calibrate=True):
    df = load_dataset(data_path)
    X = df["clean_text"]
    y = df["label_num"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Print dataset sizes used for training/testing
    n_train = len(X_train)
    n_test = len(X_test)
    total = n_train + n_test
    print(f"Dataset loaded: {os.path.abspath(data_path)}")
    print(f"Total samples: {total}")
    print(f"Training samples: {n_train}")
    print(f"Testing  samples: {n_test}")

    vect = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
    X_train_vec = vect.fit_transform(X_train)
    X_test_vec = vect.transform(X_test)

    base_clf = LinearSVC(random_state=random_state, max_iter=10000, class_weight='balanced')
    clf = CalibratedClassifierCV(base_clf, cv=3)   # ensure calibration (probabilities)

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
    parser = argparse.ArgumentParser(description="Train Linear SVM spam detector")
    parser.add_argument("--data", "-d", help="Path to CSV dataset")
    parser.add_argument("--no-calibrate", action="store_true", help="Do not calibrate probabilities (faster).")
    args = parser.parse_args()
    dataset_path = find_dataset(args.data)
    print("Using dataset:", dataset_path)
    train_and_save(dataset_path, calibrate=not args.no_calibrate)
