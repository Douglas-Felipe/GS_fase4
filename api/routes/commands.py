"""
Rotas de comandos da API LunarGrid.
Gerencia comandos manuais e pendentes para controle de setores,
incluindo a fila de comandos para consumo pelo ESP32.
"""

from fastapi import APIRouter, HTTPException
from models.schemas import CommandPayload
from database import save_command, get_pending_commands, mark_command_executed, get_commands_history

router = APIRouter(prefix="/api/commands", tags=["Comandos"])


@router.post("/")
async def create_command(payload: CommandPayload):
    """
    Cria um comando manual para controle de setor.
    Permite que o operador faça override das decisões da IA.

    Args:
        payload: Dados do comando com sector_id e action (on/off).

    Returns:
        Confirmação do comando criado com seu ID.
    """
    try:
        command_id = save_command({
            "sector_id": payload.sector_id,
            "action": payload.action,
            "source": "manual",
        })
        return {
            "message": f"Comando manual criado com sucesso.",
            "command_id": command_id,
            "sector_id": payload.sector_id,
            "action": payload.action,
            "source": "manual",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar comando: {str(e)}"
        )


@router.get("/pending")
async def pending_commands():
    """
    Retorna comandos pendentes para o ESP32 consumir.
    Após retornar, marca todos os comandos como executados.

    Este endpoint é chamado periodicamente pelo ESP32 via polling
    para obter os comandos que devem ser aplicados nos setores.

    Returns:
        Lista de comandos pendentes.
    """
    try:
        commands = get_pending_commands()

        # Marcar todos como executados após leitura
        for cmd in commands:
            mark_command_executed(cmd["id"])

        return {
            "commands": commands,
            "count": len(commands),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar comandos pendentes: {str(e)}"
        )


@router.get("/history")
async def commands_history():
    """
    Retorna o histórico dos últimos 50 comandos executados.

    Returns:
        Lista de comandos ordenados do mais recente.
    """
    try:
        history = get_commands_history(limit=50)
        return {"data": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar histórico de comandos: {str(e)}"
        )
