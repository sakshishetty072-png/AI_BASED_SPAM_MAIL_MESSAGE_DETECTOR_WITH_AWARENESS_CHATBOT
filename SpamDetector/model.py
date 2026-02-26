import os
import pickle
from text_utils import clean_text

_model = None
_vectorizer = None

def load_model_and_vectorizer(model_path=None, vec_path=None):
    """
    Load model and vectorizer. If explicit paths aren't provided, use ./models/
    inside the project directory to find:
      models/linear_svm_model.pkl
      models/vectorizer_svm.pkl
    """
    global _model, _vectorizer
    project_root = os.path.abspath(os.path.dirname(__file__))
    default_model = os.path.join(project_root, "models/models_downloaded", "linear_svm_model.pkl")
    default_vec = os.path.join(project_root, "models/models_downloaded", "vectorizer_svm.pkl")

    model_path = model_path or default_model
    vec_path = vec_path or default_vec

    if _model is None or _vectorizer is None:
        _model = pickle.load(open(model_path, "rb"))
        _vectorizer = pickle.load(open(vec_path, "rb"))
    return _model, _vectorizer

def predict_spam(email_text):
    model, vectorizer = load_model_and_vectorizer()
    cleaned = clean_text(email_text)
    vec = vectorizer.transform([cleaned])
    pred = model.predict(vec)[0]
    return "Spam" if pred == 1 else "Ham", model.predict_proba(vec)[0] 
