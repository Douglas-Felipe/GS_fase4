"""
Rotas de simulação e status da API LunarGrid.
Permite simular cenários energéticos sem persistir dados
e consultar o status atual da base lunar.
"""

from fastapi import APIRouter, HTTPException
from models.schemas import (
    SimulationPayload,
    PredictionResponse,
    TelemetryPayload,
    SectorData,
    BaseStatus,
)
from models.predictor import get_predictor
from database import get_latest_telemetry, get_commands_history, save_telemetry, save_command

router = APIRouter(prefix="/api", tags=["Simulação e Status"])

# Setores padrão da base lunar para simulações
DEFAULT_SECTORS = [
    SectorData(id=1, name="Suporte de Vida", priority=1, active=True, consumption=25.0),
    SectorData(id=2, name="Comunicações", priority=2, active=True, consumption=15.0),
    SectorData(id=3, name="Laboratório", priority=3, active=True, consumption=20.0),
    SectorData(id=4, name="Pesquisa e Conforto", priority=4, active=True, consumption=18.0),
]


@router.post("/simulate", response_model=PredictionResponse)
async def simulate_scenario(payload: SimulationPayload):
    """
    Simula um cenário energético salvando os dados de telemetria e os comandos
    gerados no banco de dados para atualizar os painéis em tempo real.
    Útil para testes de estresse e planejamento de missão.

    Args:
        payload: Parâmetros de simulação (geração solar, bateria, hora lunar).

    Returns:
        PredictionResponse com comandos sugeridos, risco e autonomia.
    """
    try:
        # Calcular consumo total dos setores padrão
        total_consumption = sum(s.consumption for s in DEFAULT_SECTORS)

        # Montar payload virtual de telemetria
        telemetry_dict = {
            "solar_generation": payload.solar_generation,
            "battery_level": payload.battery_level,
            "base_consumption": total_consumption,
            "lunar_hour": payload.lunar_hour,
            "sectors": [s.model_dump() for s in DEFAULT_SECTORS],
        }

        # Salvar telemetria simulada no banco
        save_telemetry(telemetry_dict)

        # Executar predição
        predictor = get_predictor()
        prediction = predictor.predict(telemetry_dict)

        # Salvar comandos gerados pela IA no banco
        for cmd in prediction.sector_commands:
            save_command({
                "sector_id": cmd.sector_id,
                "action": cmd.action,
                "source": "ai",
            })

        return prediction

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro na simulação: {str(e)}"
        )


@router.get("/status", response_model=BaseStatus)
async def get_status():
    """
    Retorna o status completo da base lunar com a última telemetria
    e avaliação de risco atual, aplicando os comandos mais recentes.

    Returns:
        BaseStatus com todos os dados atuais da base.
    """
    try:
        latest = get_latest_telemetry()

        # Estado base dos setores (da telemetria ou padrão)
        if latest is not None:
            sector_active = {
                1: bool(latest.get("sector_1_active", 1)),
                2: bool(latest.get("sector_2_active", 1)),
                3: bool(latest.get("sector_3_active", 1)),
                4: bool(latest.get("sector_4_active", 1)),
            }
        else:
            sector_active = {1: True, 2: True, 3: True, 4: True}

        # Aplicar os comandos mais recentes por cima do estado da telemetria
        # Isso garante que comandos manuais e da IA sejam refletidos imediatamente
        recent_cmds = get_commands_history(limit=20)
        last_per_sector = {}
        for cmd in recent_cmds:
            sid = cmd.get("sector_id")
            if sid not in last_per_sector:
                last_per_sector[sid] = {
                    "action": cmd.get("action"),
                    "source": cmd.get("source"),
                }
        for sid, info in last_per_sector.items():
            if sid in sector_active:
                sector_active[sid] = (info["action"] == "on")

        # Função para determinar o status detalhado
        def determine_status(sid, active):
            if active:
                return "active"
            cmd_info = last_per_sector.get(sid)
            if cmd_info and cmd_info["action"] == "off":
                if cmd_info["source"] == "ai":
                    return "ai_shutoff"
                elif cmd_info["source"] == "manual":
                    return "manual_shutoff"
            return "off"

        sectors = [
            SectorData(id=1, name="Suporte de Vida",     priority=1, active=sector_active[1], consumption=25.0, status=determine_status(1, sector_active[1])),
            SectorData(id=2, name="Comunicações",         priority=2, active=sector_active[2], consumption=15.0, status=determine_status(2, sector_active[2])),
            SectorData(id=3, name="Laboratório",           priority=3, active=sector_active[3], consumption=20.0, status=determine_status(3, sector_active[3])),
            SectorData(id=4, name="Pesquisa e Conforto",  priority=4, active=sector_active[4], consumption=18.0, status=determine_status(4, sector_active[4])),
        ]

        # Executar predição para obter risco atual
        predictor = get_predictor()
        if latest is not None:
            prediction = predictor.predict(latest)
            risk_level = prediction.risk_level
        else:
            risk_level = "low"

        return BaseStatus(
            solar_generation=latest.get("solar_generation", 0.0) if latest else 0.0,
            battery_level=latest.get("battery_level", 100.0) if latest else 100.0,
            base_consumption=latest.get("base_consumption", 0.0) if latest else 0.0,
            lunar_hour=latest.get("lunar_hour", 0.0) if latest else 0.0,
            sectors=sectors,
            risk_level=risk_level,
            last_update=latest.get("timestamp") if latest else None,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter status: {str(e)}"
        )
