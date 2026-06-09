"""
Módulo de banco de dados SQLite para o LunarGrid.
Gerencia conexões, criação de tabelas e operações CRUD
para telemetria e comandos.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional

# Caminho do banco de dados
DB_PATH = os.path.join(os.path.dirname(__file__), "lunargrid.db")


def get_connection() -> sqlite3.Connection:
    """Retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db():
    """
    Inicializa o banco de dados criando as tabelas necessárias
    caso ainda não existam.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de telemetria — armazena leituras dos sensores da base lunar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            solar_generation REAL NOT NULL,
            battery_level REAL NOT NULL,
            base_consumption REAL NOT NULL,
            lunar_hour REAL NOT NULL,
            sector_1_active INTEGER NOT NULL DEFAULT 1,
            sector_2_active INTEGER NOT NULL DEFAULT 1,
            sector_3_active INTEGER NOT NULL DEFAULT 1,
            sector_4_active INTEGER NOT NULL DEFAULT 1
        )
    """)

    # Tabela de comandos — ações de ligar/desligar setores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sector_id INTEGER NOT NULL,
            action TEXT NOT NULL CHECK(action IN ('on', 'off')),
            source TEXT NOT NULL CHECK(source IN ('ai', 'manual')),
            timestamp TEXT NOT NULL,
            executed INTEGER NOT NULL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Banco de dados inicializado com sucesso.")


def save_telemetry(data: dict) -> int:
    """
    Salva um registro de telemetria no banco de dados.

    Args:
        data: Dicionário com os campos de telemetria.

    Returns:
        O ID do registro inserido.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Extrair estado dos setores a partir da lista de setores
    sectors = data.get("sectors", [])
    sector_states = {s.get("id", i + 1): s.get("active", True) for i, s in enumerate(sectors)}

    cursor.execute("""
        INSERT INTO telemetry (
            timestamp, solar_generation, battery_level, base_consumption,
            lunar_hour, sector_1_active, sector_2_active, sector_3_active, sector_4_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        data.get("solar_generation", 0.0),
        data.get("battery_level", 0.0),
        data.get("base_consumption", 0.0),
        data.get("lunar_hour", 0.0),
        int(sector_states.get(1, True)),
        int(sector_states.get(2, True)),
        int(sector_states.get(3, True)),
        int(sector_states.get(4, True)),
    ))

    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def get_telemetry_history(limit: int = 50) -> list[dict]:
    """
    Retorna o histórico de telemetria ordenado do mais recente ao mais antigo.

    Args:
        limit: Número máximo de registros a retornar.

    Returns:
        Lista de dicionários com os registros de telemetria.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM telemetry
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_latest_telemetry() -> Optional[dict]:
    """
    Retorna o registro de telemetria mais recente.

    Returns:
        Dicionário com o registro ou None se não houver dados.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM telemetry
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_command(cmd: dict) -> int:
    """
    Salva um comando no banco de dados.

    Args:
        cmd: Dicionário com sector_id, action, source.

    Returns:
        O ID do comando inserido.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO commands (sector_id, action, source, timestamp, executed)
        VALUES (?, ?, ?, ?, 0)
    """, (
        cmd.get("sector_id"),
        cmd.get("action"),
        cmd.get("source", "manual"),
        datetime.now().isoformat(),
    ))

    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def get_pending_commands() -> list[dict]:
    """
    Retorna comandos pendentes (não executados) para o ESP32 consumir.

    Returns:
        Lista de comandos pendentes.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM commands
        WHERE executed = 0
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_command_executed(command_id: int) -> bool:
    """
    Marca um comando como executado.

    Args:
        command_id: ID do comando a marcar.

    Returns:
        True se o comando foi atualizado, False caso contrário.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE commands
        SET executed = 1
        WHERE id = ?
    """, (command_id,))

    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def get_commands_history(limit: int = 50) -> list[dict]:
    """
    Retorna o histórico de comandos ordenado do mais recente ao mais antigo.

    Args:
        limit: Número máximo de registros a retornar.

    Returns:
        Lista de dicionários com os comandos.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM commands
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
