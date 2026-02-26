import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report
import re

# Load the dataset
df = pd.read_csv('../dataset/spam_ham_dataset.csv')

# Inspect the first few rows and columns
print("Columns available:", df.columns)
print(df.head())

# If needed, select the correct columns for label and message
# Adjust these lines if your CSV has different column names
if 'label' in df.columns and 'text' in df.columns:
    df = df[['label', 'text']]
elif 'label' in df.columns and 'email' in df.columns:
    df = df[['label', 'email']]
else:
    # For typical Kaggle datasets, often the columns are 'label' and 'text'
    # For some, you may need to adjust this based on the output above
    pass

# Clean the text
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return text

df['clean_text'] = df[df.columns[1]].apply(clean_text)

# Convert labels to binary (adjust mapping if needed)
if df['label'].dtype == object:
    df['label_num'] = df['label'].map({'ham': 0, 'spam': 1})
else:
    df['label_num'] = df['label']

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    df['clean_text'], df['label_num'], test_size=0.2, random_state=42
)

# Vectorize text
vectorizer = TfidfVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Train the model
model = MultinomialNB()
model.fit(X_train_vec, y_train)

# Evaluate the model
y_pred = model.predict(X_test_vec)
print(classification_report(y_test, y_pred))

# Predict on a new example
def predict_spam(email_text):
    cleaned = clean_text(email_text)
    vec = vectorizer.transform([cleaned])
    pred = model.predict(vec)[0]
    return 'Spam' if pred == 1 else 'Ham'

# Example usage
print(predict_spam("Congratulations! You've won a free prize. Click here now!"))
