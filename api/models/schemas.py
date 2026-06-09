"""
Schemas Pydantic para validação de dados da API LunarGrid.
Define os modelos de entrada e saída para telemetria,
comandos, predições e status da base.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SectorData(BaseModel):
    """Dados de um setor da base lunar."""
    id: int = Field(..., description="Identificador do setor (1-4)")
    name: str = Field(..., description="Nome do setor")
    priority: int = Field(..., description="Prioridade do setor (1=mais alta)")
    active: bool = Field(True, description="Se o setor está ativo")
    consumption: float = Field(..., description="Consumo energético do setor em kW")
    status: Optional[str] = Field(None, description="Status detalhado do setor (ex: active, ai_shutoff, manual_shutoff)")


class TelemetryPayload(BaseModel):
    """Payload de telemetria recebido do ESP32."""
    solar_generation: float = Field(..., description="Geração solar atual em kW")
    battery_level: float = Field(..., ge=0, le=100, description="Nível da bateria em porcentagem")
    base_consumption: float = Field(..., description="Consumo total da base em kW")
    lunar_hour: float = Field(..., ge=0, le=720, description="Hora lunar (0-720, ciclo de ~29.5 dias terrestres)")
    sectors: list[SectorData] = Field(..., description="Lista dos setores da base")


class CommandPayload(BaseModel):
    """Payload de comando manual para controle de setor."""
    sector_id: int = Field(..., description="ID do setor alvo (1-4)")
    action: str = Field(..., pattern="^(on|off)$", description="Ação: 'on' para ligar, 'off' para desligar")


class SectorCommand(BaseModel):
    """Comando individual para um setor gerado pela IA."""
    sector_id: int = Field(..., description="ID do setor alvo")
    action: str = Field(..., description="Ação: 'on' ou 'off'")


class PredictionResponse(BaseModel):
    """Resposta da predição de risco energético da IA."""
    sector_commands: list[SectorCommand] = Field(
        default_factory=list,
        description="Lista de comandos gerados para os setores"
    )
    risk_level: str = Field(
        ...,
        pattern="^(low|medium|high|critical)$",
        description="Nível de risco: low, medium, high ou critical"
    )
    predicted_autonomy_hours: float = Field(
        ...,
        description="Autonomia estimada em horas terrestres"
    )
    message: str = Field(..., description="Mensagem descritiva sobre o estado atual")


class SimulationPayload(BaseModel):
    """Payload para simulação de cenário energético."""
    solar_generation: float = Field(..., description="Geração solar simulada em kW")
    battery_level: float = Field(..., ge=0, le=100, description="Nível de bateria simulado")
    lunar_hour: float = Field(..., ge=0, le=720, description="Hora lunar simulada")


class BaseStatus(BaseModel):
    """Status completo da base lunar."""
    solar_generation: float = Field(0.0, description="Geração solar atual em kW")
    battery_level: float = Field(0.0, description="Nível da bateria em porcentagem")
    base_consumption: float = Field(0.0, description="Consumo total da base em kW")
    lunar_hour: float = Field(0.0, description="Hora lunar atual")
    sectors: list[SectorData] = Field(default_factory=list, description="Estado dos setores")
    risk_level: str = Field("low", description="Nível de risco atual")
    last_update: Optional[str] = Field(None, description="Timestamp da última atualização")
