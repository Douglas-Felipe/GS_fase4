"""
Ponto de entrada principal da API LunarGrid.

API de gerenciamento energético inteligente para uma base lunar,
utilizando IA preditiva (Random Forest) para otimizar o consumo
de energia e prevenir colapsos energéticos.

Executar com:
    uvicorn main:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from models.predictor import get_predictor
from routes.telemetry import router as telemetry_router
from routes.commands import router as commands_router
from routes.simulation import router as simulation_router, get_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerenciador de ciclo de vida da aplicação.
    Inicializa o banco de dados e o preditor no startup.
    """
    # Startup — inicialização
    print("=" * 50)
    print("  🌙 LunarGrid API — Inicializando...")
    print("=" * 50)

    # Inicializar banco de dados
    init_db()

    # Inicializar preditor (treina se não houver modelo salvo)
    get_predictor()

    print("\n✅ LunarGrid API pronta para receber requisições!")
    print("=" * 50)

    yield  # Aplicação em execução

    # Shutdown — limpeza
    print("\n🔴 LunarGrid API encerrando...")


# Criar aplicação FastAPI
app = FastAPI(
    title="LunarGrid API",
    description=(
        "API de gerenciamento energético inteligente para base lunar. "
        "Utiliza IA preditiva baseada em Random Forest para monitorar "
        "telemetria, prever riscos de colapso energético e gerenciar "
        "automaticamente os setores da base."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configurar CORS — permitir todas as origens para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(telemetry_router)
app.include_router(commands_router)
app.include_router(simulation_router)


@app.get("/status", tags=["Status"])
async def status_alias():
    """Alias para o endpoint /api/status para evitar erros 404."""
    return await get_status()


@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raiz com informações sobre a API.

    Returns:
        Informações gerais e links para documentação.
    """
    return {
        "name": "LunarGrid API",
        "version": "1.0.0",
        "description": "API de gerenciamento energético inteligente para base lunar",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "telemetry": {
                "POST /api/telemetry/": "Enviar dados de telemetria",
                "GET /api/telemetry/history": "Histórico de telemetria",
                "GET /api/telemetry/latest": "Última telemetria",
            },
            "commands": {
                "POST /api/commands/": "Criar comando manual",
                "GET /api/commands/pending": "Comandos pendentes (ESP32)",
                "GET /api/commands/history": "Histórico de comandos",
            },
            "simulation": {
                "POST /api/simulate": "Simular cenário energético",
                "GET /api/status": "Status atual da base",
            },
        },
    }
