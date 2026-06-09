"""
Módulo de predição de risco energético para o LunarGrid.
Utiliza RandomForestClassifier para classificar o nível de risco
de colapso energético na base lunar e gerar comandos automáticos
de gerenciamento de setores.
"""

import os
import math
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from models.schemas import (
    PredictionResponse,
    SectorCommand,
    TelemetryPayload,
)

# Caminho do modelo treinado
MODEL_PATH = os.path.join(os.path.dirname(__file__), "energy_model.pkl")

# Período do ciclo lunar em horas (aproximadamente 29.5 dias terrestres = ~708h, usamos 720 para simplificar)
LUNAR_PERIOD = 720.0

# Mapeamento de labels de risco
RISK_LABELS = {0: "low", 1: "medium", 2: "high", 3: "critical"}

# Mensagens de risco em português
RISK_MESSAGES = {
    "low": "✅ Sistema operando normalmente. Todos os setores ativos.",
    "medium": "⚠️ Risco moderado detectado. Setor de pesquisa desligado para economia.",
    "high": "🔶 Risco alto! Setores não essenciais desligados. Priorizando suporte de vida e comunicações.",
    "critical": "🚨 RISCO CRÍTICO! Apenas suporte de vida ativo. Bateria em nível perigoso!",
}


class EnergyPredictor:
    """
    Preditor de risco energético baseado em Random Forest.

    Utiliza dados de telemetria (geração solar, nível de bateria,
    consumo da base e hora lunar) para prever o nível de risco
    e gerar comandos automáticos de controle de setores.
    """

    def __init__(self):
        """Inicializa o preditor, carregando modelo existente ou treinando um novo."""
        self.model: RandomForestClassifier = None
        self.is_trained = False

        # Tentar carregar modelo salvo
        if self.load_model():
            print("[PREDITOR] Modelo carregado com sucesso.")
        else:
            print("[PREDITOR] Modelo não encontrado. Treinando novo modelo...")
            self.train()
            self.save_model()
            print("[PREDITOR] Modelo treinado e salvo com sucesso.")

    def _encode_lunar_hour(self, lunar_hour: float) -> tuple[float, float]:
        """
        Codifica a hora lunar como seno e cosseno para capturar
        a natureza cíclica do período lunar.

        Args:
            lunar_hour: Hora lunar (0-720).

        Returns:
            Tupla (sin, cos) da hora lunar normalizada.
        """
        angle = 2 * math.pi * lunar_hour / LUNAR_PERIOD
        return math.sin(angle), math.cos(angle)

    def _extract_features(self, data: dict) -> np.ndarray:
        """
        Extrai as features do dicionário de telemetria para alimentar o modelo.

        Args:
            data: Dicionário com dados de telemetria.

        Returns:
            Array numpy com as features: [solar_generation, battery_level,
            base_consumption, lunar_hour_sin, lunar_hour_cos]
        """
        solar = data.get("solar_generation", 0.0)
        battery = data.get("battery_level", 0.0)
        consumption = data.get("base_consumption", 0.0)
        lunar_hour = data.get("lunar_hour", 0.0)

        lh_sin, lh_cos = self._encode_lunar_hour(lunar_hour)

        return np.array([[solar, battery, consumption, lh_sin, lh_cos]])

    def predict(self, telemetry_data: dict) -> PredictionResponse:
        """
        Realiza a predição de risco energético e gera comandos de setores.

        Args:
            telemetry_data: Dicionário com dados de telemetria.

        Returns:
            PredictionResponse com comandos, nível de risco, autonomia e mensagem.
        """
        features = self._extract_features(telemetry_data)

        # Obter probabilidades de cada classe de risco
        if self.model and self.is_trained:
            probabilities = self.model.predict_proba(features)[0]
            # Calcular score ponderado de risco (0-1)
            risk_score = sum(i * p for i, p in enumerate(probabilities)) / 3.0
            predicted_class = int(self.model.predict(features)[0])
        else:
            # Fallback sem modelo: usar heurística simples
            risk_score = self._heuristic_risk(telemetry_data)
            predicted_class = self._score_to_class(risk_score)

        # Determinar nível de risco
        risk_level = RISK_LABELS.get(predicted_class, "low")

        # Calcular autonomia prevista em horas
        battery = telemetry_data.get("battery_level", 0.0)
        consumption = telemetry_data.get("base_consumption", 0.0)
        generation = telemetry_data.get("solar_generation", 0.0)
        net_consumption = max(consumption - generation, 1.0)

        # Fator de tempo: bateria_% / consumo_líquido * fator_escala
        time_factor = 2.5  # Fator de escala para horas terrestres
        predicted_autonomy = round((battery / net_consumption) * time_factor, 1)

        # Lógica de decisão para comandos de setores
        commands = self._generate_sector_commands(risk_level)

        # Mensagem descritiva
        message = RISK_MESSAGES.get(risk_level, RISK_MESSAGES["low"])

        return PredictionResponse(
            sector_commands=commands,
            risk_level=risk_level,
            predicted_autonomy_hours=predicted_autonomy,
            message=message,
        )

    def _heuristic_risk(self, data: dict) -> float:
        """
        Calcula risco heurístico quando não há modelo treinado.

        Args:
            data: Dicionário com dados de telemetria.

        Returns:
            Score de risco entre 0 e 1.
        """
        battery = data.get("battery_level", 50.0)
        solar = data.get("solar_generation", 0.0)
        consumption = data.get("base_consumption", 0.0)

        # Risco aumenta com bateria baixa e consumo > geração
        battery_risk = max(0, 1 - battery / 100)
        energy_balance_risk = max(0, min(1, (consumption - solar) / max(consumption, 1)))

        return 0.6 * battery_risk + 0.4 * energy_balance_risk

    def _score_to_class(self, score: float) -> int:
        """Converte score de risco em classe."""
        if score < 0.3:
            return 0  # low
        elif score < 0.6:
            return 1  # medium
        elif score < 0.8:
            return 2  # high
        else:
            return 3  # critical

    def _generate_sector_commands(self, risk_level: str) -> list[SectorCommand]:
        """
        Gera comandos para os setores baseado no nível de risco.

        Hierarquia de prioridade dos setores:
        - Setor 1: Suporte de Vida (prioridade máxima — nunca desliga)
        - Setor 2: Comunicações (prioridade alta)
        - Setor 3: Laboratório (prioridade média)
        - Setor 4: Pesquisa e Conforto (prioridade baixa)

        Args:
            risk_level: Nível de risco atual.

        Returns:
            Lista de SectorCommand com ações para cada setor.
        """
        commands = []

        if risk_level == "critical":
            # Crítico: apenas suporte de vida ativo
            commands = [
                SectorCommand(sector_id=1, action="on"),
                SectorCommand(sector_id=2, action="off"),
                SectorCommand(sector_id=3, action="off"),
                SectorCommand(sector_id=4, action="off"),
            ]
        elif risk_level == "high":
            # Alto: desligar setores 3 e 4
            commands = [
                SectorCommand(sector_id=1, action="on"),
                SectorCommand(sector_id=2, action="on"),
                SectorCommand(sector_id=3, action="off"),
                SectorCommand(sector_id=4, action="off"),
            ]
        elif risk_level == "medium":
            # Médio: desligar setor 4
            commands = [
                SectorCommand(sector_id=1, action="on"),
                SectorCommand(sector_id=2, action="on"),
                SectorCommand(sector_id=3, action="on"),
                SectorCommand(sector_id=4, action="off"),
            ]
        else:
            # Baixo: tudo ligado
            commands = [
                SectorCommand(sector_id=1, action="on"),
                SectorCommand(sector_id=2, action="on"),
                SectorCommand(sector_id=3, action="on"),
                SectorCommand(sector_id=4, action="on"),
            ]

        return commands

    def train(self):
        """
        Treina o modelo com dados sintéticos que simulam cenários
        energéticos reais de uma base lunar.

        Gera ~2000 amostras cobrindo:
        - Dia lunar (hora 0-360): alta geração solar, bateria carregando
        - Transição dia→noite (hora 300-400): solar caindo
        - Noite lunar (hora 360-720): sem solar, bateria drenando
        - Cenários críticos: bateria < 20% sem solar
        """
        np.random.seed(42)
        samples = []

        # --- Cenário 1: Dia lunar (hora 0-360) — risco baixo ---
        for _ in range(500):
            lunar_hour = np.random.uniform(0, 300)
            solar = np.random.uniform(60, 100)  # Alta geração solar
            battery = np.random.uniform(50, 100)  # Bateria carregando
            consumption = np.random.uniform(30, 70)
            risk = 0  # low
            samples.append([solar, battery, consumption, lunar_hour, risk])

        # --- Cenário 2: Transição dia→noite (hora 300-400) — risco médio ---
        for _ in range(400):
            lunar_hour = np.random.uniform(300, 400)
            # Solar diminuindo gradualmente
            progress = (lunar_hour - 300) / 100  # 0 a 1
            solar = np.random.uniform(10, 60) * (1 - progress * 0.8)
            battery = np.random.uniform(30, 80)
            consumption = np.random.uniform(40, 75)
            risk = 1  # medium
            samples.append([solar, battery, consumption, lunar_hour, risk])

        # --- Cenário 3: Noite lunar com bateria boa (hora 360-720) — risco médio/alto ---
        for _ in range(300):
            lunar_hour = np.random.uniform(360, 720)
            solar = np.random.uniform(0, 5)  # Sem geração solar
            battery = np.random.uniform(40, 80)  # Bateria ainda razoável
            consumption = np.random.uniform(40, 70)
            risk = 1  # medium
            samples.append([solar, battery, consumption, lunar_hour, risk])

        # --- Cenário 4: Noite lunar com bateria caindo (hora 360-720) — risco alto ---
        for _ in range(400):
            lunar_hour = np.random.uniform(360, 720)
            solar = np.random.uniform(0, 3)
            battery = np.random.uniform(20, 45)  # Bateria baixa
            consumption = np.random.uniform(45, 80)
            risk = 2  # high
            samples.append([solar, battery, consumption, lunar_hour, risk])

        # --- Cenário 5: Situação crítica — bateria muito baixa ---
        for _ in range(300):
            lunar_hour = np.random.uniform(400, 720)
            solar = np.random.uniform(0, 2)
            battery = np.random.uniform(0, 20)  # Bateria perigosamente baixa
            consumption = np.random.uniform(50, 90)
            risk = 3  # critical
            samples.append([solar, battery, consumption, lunar_hour, risk])

        # --- Cenário 6: Dia com bateria baixa (recuperação) — risco médio ---
        for _ in range(100):
            lunar_hour = np.random.uniform(0, 200)
            solar = np.random.uniform(50, 90)
            battery = np.random.uniform(10, 35)  # Bateria baixa, mas com sol
            consumption = np.random.uniform(30, 60)
            risk = 1  # medium — sol está carregando
            samples.append([solar, battery, consumption, lunar_hour, risk])

        # Converter para DataFrame
        df = pd.DataFrame(samples, columns=[
            "solar_generation", "battery_level", "base_consumption",
            "lunar_hour", "risk_label"
        ])

        # Codificar hora lunar como sin/cos
        df["lunar_hour_sin"] = np.sin(2 * np.pi * df["lunar_hour"] / LUNAR_PERIOD)
        df["lunar_hour_cos"] = np.cos(2 * np.pi * df["lunar_hour"] / LUNAR_PERIOD)

        # Features e target
        feature_cols = [
            "solar_generation", "battery_level", "base_consumption",
            "lunar_hour_sin", "lunar_hour_cos"
        ]
        X = df[feature_cols].values
        y = df["risk_label"].values.astype(int)

        # Dividir em treino e teste
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Treinar Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight="balanced",
        )
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Métricas de acurácia
        accuracy = self.model.score(X_test, y_test)
        print(f"[PREDITOR] Acurácia do modelo: {accuracy:.4f}")

        # Relatório de classificação
        y_pred = self.model.predict(X_test)
        report = classification_report(
            y_test, y_pred,
            target_names=["low", "medium", "high", "critical"],
        )
        print(f"[PREDITOR] Relatório de classificação:\n{report}")

    def save_model(self):
        """Salva o modelo treinado em disco usando joblib."""
        if self.model:
            joblib.dump(self.model, MODEL_PATH)
            print(f"[PREDITOR] Modelo salvo em: {MODEL_PATH}")

    def load_model(self) -> bool:
        """
        Carrega o modelo salvo do disco.

        Returns:
            True se o modelo foi carregado com sucesso, False caso contrário.
        """
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                self.is_trained = True
                return True
            except Exception as e:
                print(f"[PREDITOR] Erro ao carregar modelo: {e}")
                return False
        return False


# Instância singleton do preditor
_predictor_instance: EnergyPredictor = None


def get_predictor() -> EnergyPredictor:
    """
    Retorna a instância singleton do preditor.
    Cria uma nova instância se necessário.
    """
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = EnergyPredictor()
    return _predictor_instance
