"""
Script autônomo de treinamento do modelo de predição energética.

Gera dados sintéticos simulando cenários reais de uma base lunar,
treina um RandomForestClassifier, imprime métricas de acurácia
e salva o modelo em api/models/energy_model.pkl.

Uso:
    python -m models.train
    ou
    python models/train.py
"""

import os
import sys
import math
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# Caminho do modelo
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "energy_model.pkl")

# Período lunar
LUNAR_PERIOD = 720.0


def generate_synthetic_data() -> pd.DataFrame:
    """
    Gera dataset sintético simulando cenários energéticos de uma base lunar.

    Cenários cobertos:
    1. Dia lunar (hora 0-300): alta geração solar → risco baixo
    2. Transição dia→noite (hora 300-400): solar caindo → risco crescente
    3. Noite com bateria boa (hora 360-720): sem solar, bateria OK → risco médio
    4. Noite com bateria baixa (hora 360-720): bateria caindo → risco alto
    5. Situação crítica: bateria < 20% sem solar → risco crítico
    6. Dia com bateria baixa: recuperação com sol → risco médio

    Returns:
        DataFrame com features e labels de risco.
    """
    np.random.seed(42)
    samples = []

    # Cenário 1: Dia lunar — risco baixo
    for _ in range(500):
        lunar_hour = np.random.uniform(0, 300)
        solar = np.random.uniform(60, 100)
        battery = np.random.uniform(50, 100)
        consumption = np.random.uniform(30, 70)
        samples.append([solar, battery, consumption, lunar_hour, 0])

    # Cenário 2: Transição dia→noite — risco médio
    for _ in range(400):
        lunar_hour = np.random.uniform(300, 400)
        progress = (lunar_hour - 300) / 100
        solar = np.random.uniform(10, 60) * (1 - progress * 0.8)
        battery = np.random.uniform(30, 80)
        consumption = np.random.uniform(40, 75)
        samples.append([solar, battery, consumption, lunar_hour, 1])

    # Cenário 3: Noite com bateria boa — risco médio
    for _ in range(300):
        lunar_hour = np.random.uniform(360, 720)
        solar = np.random.uniform(0, 5)
        battery = np.random.uniform(40, 80)
        consumption = np.random.uniform(40, 70)
        samples.append([solar, battery, consumption, lunar_hour, 1])

    # Cenário 4: Noite com bateria baixa — risco alto
    for _ in range(400):
        lunar_hour = np.random.uniform(360, 720)
        solar = np.random.uniform(0, 3)
        battery = np.random.uniform(20, 45)
        consumption = np.random.uniform(45, 80)
        samples.append([solar, battery, consumption, lunar_hour, 2])

    # Cenário 5: Situação crítica
    for _ in range(300):
        lunar_hour = np.random.uniform(400, 720)
        solar = np.random.uniform(0, 2)
        battery = np.random.uniform(0, 20)
        consumption = np.random.uniform(50, 90)
        samples.append([solar, battery, consumption, lunar_hour, 3])

    # Cenário 6: Dia com bateria baixa — risco médio (recuperação)
    for _ in range(100):
        lunar_hour = np.random.uniform(0, 200)
        solar = np.random.uniform(50, 90)
        battery = np.random.uniform(10, 35)
        consumption = np.random.uniform(30, 60)
        samples.append([solar, battery, consumption, lunar_hour, 1])

    df = pd.DataFrame(samples, columns=[
        "solar_generation", "battery_level", "base_consumption",
        "lunar_hour", "risk_label"
    ])

    # Codificar hora lunar como sin/cos (natureza cíclica)
    df["lunar_hour_sin"] = np.sin(2 * np.pi * df["lunar_hour"] / LUNAR_PERIOD)
    df["lunar_hour_cos"] = np.cos(2 * np.pi * df["lunar_hour"] / LUNAR_PERIOD)

    return df


def train_model():
    """
    Treina o modelo RandomForest e salva em disco.

    Imprime métricas detalhadas de acurácia incluindo:
    - Acurácia geral
    - Relatório de classificação por classe
    - Matriz de confusão
    - Importância das features
    """
    print("=" * 60)
    print("  LunarGrid — Treinamento do Modelo de Risco Energético")
    print("=" * 60)

    # Gerar dados
    print("\n📊 Gerando dataset sintético...")
    df = generate_synthetic_data()
    print(f"   Total de amostras: {len(df)}")
    print(f"   Distribuição de classes:")
    risk_names = {0: "low", 1: "medium", 2: "high", 3: "critical"}
    for label, name in risk_names.items():
        count = len(df[df["risk_label"] == label])
        print(f"     {name}: {count} ({count / len(df) * 100:.1f}%)")

    # Preparar features
    feature_cols = [
        "solar_generation", "battery_level", "base_consumption",
        "lunar_hour_sin", "lunar_hour_cos"
    ]
    X = df[feature_cols].values
    y = df["risk_label"].values.astype(int)

    # Dividir treino/teste
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n📦 Divisão treino/teste: {len(X_train)}/{len(X_test)}")

    # Treinar modelo
    print("\n🤖 Treinando RandomForestClassifier...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    # Avaliar modelo
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n✅ Acurácia geral: {accuracy:.4f} ({accuracy * 100:.1f}%)")

    print(f"\n📋 Relatório de Classificação:")
    print(classification_report(
        y_test, y_pred,
        target_names=["low", "medium", "high", "critical"],
    ))

    print(f"📊 Matriz de Confusão:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"              low  med  high crit")
    for i, row in enumerate(cm):
        label = ["low  ", "med  ", "high ", "crit "][i]
        print(f"   {label}  {row}")

    # Importância das features
    print(f"\n🔍 Importância das Features:")
    for name, importance in zip(feature_cols, model.feature_importances_):
        bar = "█" * int(importance * 40)
        print(f"   {name:25s} {importance:.4f} {bar}")

    # Salvar modelo
    joblib.dump(model, MODEL_PATH)
    print(f"\n💾 Modelo salvo em: {MODEL_PATH}")
    print("=" * 60)

    return model


if __name__ == "__main__":
    train_model()
