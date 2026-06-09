"""
Rotas de telemetria da API LunarGrid.
Recebe dados dos sensores do ESP32, armazena no banco
e executa predição de risco energético via IA.
"""

from fastapi import APIRouter, HTTPException
from models.schemas import TelemetryPayload, PredictionResponse
from models.predictor import get_predictor
from database import save_telemetry, get_telemetry_history, get_latest_telemetry, save_command

router = APIRouter(prefix="/api/telemetry", tags=["Telemetria"])


@router.post("/", response_model=PredictionResponse)
async def receive_telemetry(payload: TelemetryPayload):
    """
    Recebe dados de telemetria do ESP32, salva no banco de dados,
    executa predição de risco e gera comandos automáticos.

    Args:
        payload: Dados de telemetria com geração solar, bateria,
                 consumo, hora lunar e estado dos setores.

    Returns:
        PredictionResponse com comandos da IA, nível de risco e autonomia.
    """
    try:
        # Converter payload para dicionário
        telemetry_dict = payload.model_dump()

        # Converter setores para lista de dicts
        telemetry_dict["sectors"] = [s.model_dump() for s in payload.sectors]

        # Salvar telemetria no banco
        save_telemetry(telemetry_dict)

        # Executar predição de risco
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
            detail=f"Erro ao processar telemetria: {str(e)}"
        )


@router.get("/history")
async def telemetry_history():
    """
    Retorna o histórico das últimas 50 leituras de telemetria.

    Returns:
        Lista de registros de telemetria ordenados do mais recente.
    """
    try:
        history = get_telemetry_history(limit=50)
        return {"data": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar histórico: {str(e)}"
        )


@router.get("/latest")
async def latest_telemetry():
    """
    Retorna o registro de telemetria mais recente.

    Returns:
        Último registro de telemetria ou mensagem de erro se vazio.
    """
    try:
        latest = get_latest_telemetry()
        if latest is None:
            return {"data": None, "message": "Nenhum dado de telemetria encontrado."}
        return {"data": latest}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar telemetria: {str(e)}"
        )
