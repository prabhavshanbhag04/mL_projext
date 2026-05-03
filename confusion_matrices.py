import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import zscore
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, accuracy_score

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (RandomForestClassifier, AdaBoostClassifier,
                               GradientBoostingClassifier)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from xgboost import XGBClassifier

# ── 1. Load ──────────────────────────────────────────────────────────────────
df = pd.read_csv('household_power_consumption.csv', sep=',', low_memory=False)

# ── 2. Preprocess ────────────────────────────────────────────────────────────
df.replace('?', np.nan, inplace=True)

numeric_cols = [
    'Global_active_power', 'Global_reactive_power', 'Voltage',
    'Global_intensity', 'Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3'
]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# ── 3. Outlier removal ───────────────────────────────────────────────────────
df_cleaned = df.copy()
for col in numeric_cols:
    col_z = np.abs(zscore(df_cleaned[col].dropna()))
    outlier_idx = df_cleaned[col].dropna()[col_z > 3].index
    df_cleaned.drop(outlier_idx, inplace=True)

# ── 4. Binary target ─────────────────────────────────────────────────────────
median_gap = df_cleaned['Global_active_power'].median()
df_cleaned['high_consumption'] = (df_cleaned['Global_active_power'] > median_gap).astype(int)

# ── 5. Features & split ──────────────────────────────────────────────────────
feature_cols = ['Global_reactive_power', 'Voltage', 'Global_intensity',
                'Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3']

X = df_cleaned[feature_cols].dropna()
y = df_cleaned.loc[X.index, 'high_consumption']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# ── 6. Models ────────────────────────────────────────────────────────────────
models = {
    'Logistic Regression': LogisticRegression(random_state=42, solver='liblinear', max_iter=1000),
    'Decision Tree':       DecisionTreeClassifier(random_state=42),
    'Random Forest':       RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
    'KNN':                 KNeighborsClassifier(n_neighbors=5),
    'SVM':                 SVC(kernel='rbf', random_state=42),
    'Naive Bayes':         GaussianNB(),
    'AdaBoost':            AdaBoostClassifier(
                               estimator=DecisionTreeClassifier(max_depth=1, random_state=42),
                               n_estimators=50, learning_rate=1.0, random_state=42),
    'Gradient Boosting':   GradientBoostingClassifier(n_estimators=100, random_state=42),
    'XGBoost':             XGBClassifier(n_estimators=100, random_state=42,
                                         use_label_encoder=False, eval_metric='logloss',
                                         n_jobs=-1),
}

# ── 7. Plot confusion matrices ───────────────────────────────────────────────
def plot_confusion_matrix(cm, model_name):
    fig, ax = plt.subplots(figsize=(6, 5))

    sns.heatmap(cm, annot=False, cmap='Blues', linewidths=0.5,
                linecolor='gray', ax=ax,
                vmin=cm.min(), vmax=cm.max())

    # Annotate each cell — white text on dark, blue text on light
    thresh = (cm.max() + cm.min()) / 2.0
    for i in range(2):
        for j in range(2):
            color = 'white' if cm[i, j] > thresh else '#1f6eb5'
            ax.text(j + 0.5, i + 0.5, str(cm[i, j]),
                    ha='center', va='center',
                    fontsize=18, fontweight='normal', color=color)

    ax.set_title(f'Confusion Matrix - {model_name}', fontsize=13, pad=12)
    ax.set_xlabel('Predicted label', fontsize=11)
    ax.set_ylabel('True label', fontsize=11)
    ax.set_xticklabels(['0', '1'], fontsize=11)
    ax.set_yticklabels(['0', '1'], fontsize=11, rotation=0)

    plt.tight_layout()
    filename = f"cm_{model_name.replace(' ', '_').replace('(', '').replace(')', '')}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"Saved: {filename}  |  Accuracy: {accuracy_score(y_test, y_pred)*100:.2f}%\n")


for name, model in models.items():
    print(f"Training {name}...")
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_test_scaled)
    cm = confusion_matrix(y_test, y_pred)
    plot_confusion_matrix(cm, name)
