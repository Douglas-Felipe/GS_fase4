// =============================================================================
// LunarGrid - Firmware ESP32 (PlatformIO)
// Sistema de Gerenciamento Energético para Base Lunar
// =============================================================================
// Este firmware simula sensores de uma base lunar e envia telemetria para a API.
// Ele controla 4 LEDs representando setores da base, recebendo comandos da API
// para ligar/desligar setores com base na disponibilidade energética.
// =============================================================================
// Estrutura PlatformIO:
//   - platformio.ini  -> configuração do projeto e dependências
//   - wokwi.toml      -> integração com simulador Wokwi
//   - diagram.json    -> diagrama do circuito (ESP32 + 4 LEDs)
//   - src/main.cpp    -> este arquivo (código principal)
// =============================================================================

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// =============================================================================
// CONFIGURAÇÕES DE REDE
// =============================================================================
// SSID e senha do WiFi (Wokwi usa "Wokwi-GUEST" sem senha)
const char* WIFI_SSID     = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

// Endereço da API - ALTERE PARA O IP/HOST DO SEU SERVIDOR
// Exemplo: "192.168.1.100" ou "seu-servidor.com"
#define API_HOST "HOST_DA_API"
#define API_PORT 8000
#define API_TELEMETRY_PATH "/api/telemetry"
#define API_COMMANDS_PATH  "/api/commands/pending"

// =============================================================================
// DEFINIÇÃO DOS PINOS GPIO PARA OS LEDs DOS SETORES
// =============================================================================
// Cada LED representa um setor da base lunar
#define LED_LIFE_SUPPORT   2    // GPIO 2  - Suporte à Vida (Prioridade 1 - Crítico)
#define LED_COMMS          4    // GPIO 4  - Comunicações com a Terra (Prioridade 2 - Alta)
#define LED_RESEARCH_LAB   5    // GPIO 5  - Laboratório de Pesquisa (Prioridade 3 - Média)
#define LED_ROVER_MINING   18   // GPIO 18 - Recarga de Rovers/Mineração (Prioridade 4 - Baixa)

// =============================================================================
// CONSTANTES DE SIMULAÇÃO
// =============================================================================
// Intervalo de envio de telemetria (30 segundos para demonstração)
#define TELEMETRY_INTERVAL_MS 30000

// Intervalo de polling de comandos pendentes (15 segundos)
#define COMMAND_POLL_INTERVAL_MS 15000

// Ciclo lunar completo em "horas lunares" (0-720, ~29.5 dias terrestres)
#define LUNAR_CYCLE_HOURS 720

// Incremento da hora lunar a cada ciclo de telemetria
// Avança mais rápido para fins de demonstração
#define LUNAR_HOUR_INCREMENT 5

// Geração solar máxima em Watts
#define MAX_SOLAR_GENERATION 100.0

// Capacidade máxima da bateria em Wh
#define MAX_BATTERY_CAPACITY 100.0

// Nível inicial da bateria (%)
#define INITIAL_BATTERY_LEVEL 75.0

// Taxa de eficiência da carga/descarga da bateria
#define BATTERY_EFFICIENCY 0.9

// =============================================================================
// CONSUMO DE CADA SETOR (em Watts)
// =============================================================================
#define CONSUMPTION_LIFE_SUPPORT  30.0  // Suporte à Vida - sempre essencial
#define CONSUMPTION_COMMS         20.0  // Comunicações com a Terra
#define CONSUMPTION_RESEARCH_LAB  25.0  // Laboratório de Pesquisa
#define CONSUMPTION_ROVER_MINING  25.0  // Recarga de Rovers/Mineração

// =============================================================================
// ESTRUTURA DE DADOS PARA CADA SETOR
// =============================================================================
struct Sector {
  int id;                   // Identificador único do setor
  const char* name;         // Nome do setor
  int priority;             // Prioridade (1 = mais crítico)
  bool active;              // Estado atual (ligado/desligado)
  float consumption;        // Consumo em Watts quando ativo
  int ledPin;               // Pino GPIO do LED correspondente
};

// =============================================================================
// VARIÁVEIS GLOBAIS
// =============================================================================

// Array com os 4 setores da base lunar
Sector sectors[4] = {
  {1, "Suporte a Vida",           1, true,  CONSUMPTION_LIFE_SUPPORT,  LED_LIFE_SUPPORT},
  {2, "Comunicacoes Terra",       2, true,  CONSUMPTION_COMMS,         LED_COMMS},
  {3, "Laboratorio Pesquisa",     3, true,  CONSUMPTION_RESEARCH_LAB,  LED_RESEARCH_LAB},
  {4, "Recarga Rovers/Mineracao", 4, false, CONSUMPTION_ROVER_MINING,  LED_ROVER_MINING}
};

// Variáveis de simulação
float lunarHour       = 0.0;    // Hora lunar atual (0-720)
float batteryLevel    = INITIAL_BATTERY_LEVEL;  // Nível da bateria (0-100%)
float solarGeneration = 0.0;    // Geração solar atual em Watts
float baseConsumption = 0.0;    // Consumo total da base em Watts

// Controle de tempo
unsigned long lastTelemetryTime = 0;  // Último envio de telemetria
unsigned long lastCommandPoll   = 0;  // Último polling de comandos

// =============================================================================
// PROTÓTIPOS DAS FUNÇÕES
// =============================================================================
// PlatformIO requer declaração prévia das funções (diferente da Arduino IDE)
void configurarPinosLED();
void atualizarLEDs();
void conectarWiFi();
void atualizarSimulacao();
void enviarTelemetria();
void processarComandosResposta(String resposta);
void buscarComandosPendentes();
void processarComandosPendentes(String resposta);
void executarComandoSetor(int sectorId, const char* acao);

// =============================================================================
// SETUP - Inicialização do sistema
// =============================================================================
void setup() {
  // Inicializa comunicação serial para debug
  Serial.begin(115200);
  delay(1000);

  Serial.println("==============================================");
  Serial.println("  LunarGrid - Sistema de Energia Lunar");
  Serial.println("  Firmware ESP32 v1.0 (PlatformIO)");
  Serial.println("==============================================");
  Serial.println();

  // Configura os pinos dos LEDs como saída
  configurarPinosLED();

  // Liga os LEDs dos setores ativos inicialmente
  atualizarLEDs();

  // Conecta ao WiFi
  conectarWiFi();

  Serial.println("[SISTEMA] Inicialização completa!");
  Serial.println();
}

// =============================================================================
// LOOP PRINCIPAL
// =============================================================================
void loop() {
  unsigned long agora = millis();

  // Verifica se está conectado ao WiFi, reconecta se necessário
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WIFI] Conexão perdida! Tentando reconectar...");
    conectarWiFi();
  }

  // Envia telemetria a cada TELEMETRY_INTERVAL_MS (30 segundos)
  if (agora - lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryTime = agora;

    // Atualiza a simulação dos sensores
    atualizarSimulacao();

    // Envia dados de telemetria para a API
    enviarTelemetria();
  }

  // Faz polling de comandos pendentes a cada COMMAND_POLL_INTERVAL_MS (15 segundos)
  if (agora - lastCommandPoll >= COMMAND_POLL_INTERVAL_MS) {
    lastCommandPoll = agora;
    buscarComandosPendentes();
  }

  // Pequeno delay para não sobrecarregar o processador
  delay(100);
}

// =============================================================================
// CONFIGURAÇÃO DOS PINOS DOS LEDs
// =============================================================================
void configurarPinosLED() {
  Serial.println("[LED] Configurando pinos dos LEDs dos setores...");

  for (int i = 0; i < 4; i++) {
    pinMode(sectors[i].ledPin, OUTPUT);
    Serial.print("  - ");
    Serial.print(sectors[i].name);
    Serial.print(" -> GPIO ");
    Serial.println(sectors[i].ledPin);
  }

  Serial.println("[LED] Pinos configurados com sucesso!");
}

// =============================================================================
// ATUALIZAÇÃO DOS LEDs CONFORME ESTADO DOS SETORES
// =============================================================================
void atualizarLEDs() {
  for (int i = 0; i < 4; i++) {
    // Liga o LED se o setor estiver ativo, desliga caso contrário
    digitalWrite(sectors[i].ledPin, sectors[i].active ? HIGH : LOW);
  }
}

// =============================================================================
// CONEXÃO WiFi
// =============================================================================
void conectarWiFi() {
  Serial.print("[WIFI] Conectando a ");
  Serial.print(WIFI_SSID);
  Serial.print("...");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  // Aguarda conexão com timeout de 20 segundos
  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 40) {
    delay(500);
    Serial.print(".");
    tentativas++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" Conectado!");
    Serial.print("[WIFI] Endereço IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println(" FALHA na conexão!");
    Serial.println("[WIFI] Continuando sem WiFi, tentará reconectar depois.");
  }
}

// =============================================================================
// SIMULAÇÃO DOS SENSORES
// =============================================================================
// Esta função atualiza todos os valores simulados dos sensores:
// - Avança a hora lunar
// - Calcula a geração solar baseada no ciclo lunar (função cosseno)
// - Calcula o consumo total dos setores ativos
// - Atualiza o nível da bateria (carga/descarga)
// =============================================================================
void atualizarSimulacao() {
  // --- Avança a hora lunar ---
  // Incrementa e faz wrap-around quando chega ao fim do ciclo
  lunarHour += LUNAR_HOUR_INCREMENT;
  if (lunarHour >= LUNAR_CYCLE_HOURS) {
    lunarHour = 0;
    Serial.println("[LUNAR] === NOVO CICLO LUNAR INICIADO ===");
  }

  // --- Calcula a geração solar ---
  // Usa função cosseno para simular o dia/noite lunar
  // Pico de geração no "meio-dia lunar" (hora 0/720)
  // Zero de geração na "noite lunar" (hora 360)
  float lunarRadians = (lunarHour / LUNAR_CYCLE_HOURS) * 2.0 * PI;
  solarGeneration = max(0.0f, cos(lunarRadians)) * MAX_SOLAR_GENERATION;

  // --- Calcula o consumo total da base ---
  baseConsumption = 0.0;
  for (int i = 0; i < 4; i++) {
    if (sectors[i].active) {
      baseConsumption += sectors[i].consumption;
    }
  }

  // --- Atualiza o nível da bateria ---
  // Diferença entre geração e consumo (energia líquida)
  float energiaLiquida = solarGeneration - baseConsumption;

  // Converte a diferença de potência em variação de nível de bateria
  // Escala ajustada para a demonstração (intervalo de 30 segundos)
  float deltaBateria = (energiaLiquida / MAX_BATTERY_CAPACITY) * BATTERY_EFFICIENCY;

  // Aplica a variação ao nível da bateria
  batteryLevel += deltaBateria;

  // Limita o nível da bateria entre 0% e 100%
  if (batteryLevel > 100.0) batteryLevel = 100.0;
  if (batteryLevel < 0.0) batteryLevel = 0.0;

  // --- Exibe informações no Serial Monitor ---
  Serial.println("----------------------------------------------");
  Serial.println("[SIMULAÇÃO] Atualização dos sensores:");
  Serial.print("  Hora Lunar: ");
  Serial.print(lunarHour, 1);
  Serial.print(" / ");
  Serial.println(LUNAR_CYCLE_HOURS);

  Serial.print("  Geração Solar: ");
  Serial.print(solarGeneration, 2);
  Serial.println(" W");

  Serial.print("  Consumo Base: ");
  Serial.print(baseConsumption, 2);
  Serial.println(" W");

  Serial.print("  Bateria: ");
  Serial.print(batteryLevel, 2);
  Serial.println(" %");

  Serial.print("  Balanço Energético: ");
  Serial.print(energiaLiquida, 2);
  Serial.println(" W");

  // Exibe estado dos setores
  Serial.println("  Setores:");
  for (int i = 0; i < 4; i++) {
    Serial.print("    [");
    Serial.print(sectors[i].active ? "ON " : "OFF");
    Serial.print("] ");
    Serial.print(sectors[i].name);
    Serial.print(" (");
    Serial.print(sectors[i].consumption, 0);
    Serial.println(" W)");
  }
  Serial.println("----------------------------------------------");
}

// =============================================================================
// ENVIO DE TELEMETRIA VIA HTTP POST
// =============================================================================
// Monta o payload JSON com dados dos sensores e setores,
// envia para a API e processa comandos retornados na resposta.
// =============================================================================
void enviarTelemetria() {
  // Verifica conexão WiFi antes de tentar enviar
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[TELEMETRIA] Sem conexão WiFi. Envio cancelado.");
    return;
  }

  HTTPClient http;

  // Monta a URL completa da API
  String url = "http://";
  url += API_HOST;
  url += ":";
  url += API_PORT;
  url += API_TELEMETRY_PATH;

  Serial.print("[TELEMETRIA] Enviando para: ");
  Serial.println(url);

  // --- Monta o documento JSON ---
  // Usa JsonDocument (ArduinoJson v7) para criação do payload
  JsonDocument doc;

  doc["solar_generation"] = solarGeneration;
  doc["battery_level"]    = batteryLevel;
  doc["base_consumption"] = baseConsumption;
  doc["lunar_hour"]       = lunarHour;

  // Array de setores com informações detalhadas
  JsonArray sectorsArray = doc["sectors"].to<JsonArray>();

  for (int i = 0; i < 4; i++) {
    JsonObject sectorObj = sectorsArray.add<JsonObject>();
    sectorObj["id"]          = sectors[i].id;
    sectorObj["name"]        = sectors[i].name;
    sectorObj["priority"]    = sectors[i].priority;
    sectorObj["active"]      = sectors[i].active;
    sectorObj["consumption"] = sectors[i].consumption;
  }

  // Serializa o JSON para string
  String payload;
  serializeJson(doc, payload);

  Serial.print("[TELEMETRIA] Payload: ");
  Serial.println(payload);

  // --- Envia a requisição HTTP POST ---
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  int httpCode = http.POST(payload);

  // --- Processa a resposta ---
  if (httpCode > 0) {
    Serial.print("[TELEMETRIA] Código HTTP: ");
    Serial.println(httpCode);

    if (httpCode == HTTP_CODE_OK || httpCode == 201) {
      String resposta = http.getString();
      Serial.print("[TELEMETRIA] Resposta: ");
      Serial.println(resposta);

      // Processa comandos de setores na resposta
      processarComandosResposta(resposta);
    }
  } else {
    Serial.print("[TELEMETRIA] Erro na requisição: ");
    Serial.println(http.errorToString(httpCode));
  }

  http.end();
}

// =============================================================================
// PROCESSAMENTO DE COMANDOS DA RESPOSTA DA API
// =============================================================================
// Espera um JSON no formato:
// {
//   "sector_commands": [
//     {"sector_id": 1, "action": "on"},
//     {"sector_id": 4, "action": "off"}
//   ]
// }
// =============================================================================
void processarComandosResposta(String resposta) {
  JsonDocument doc;

  // Tenta fazer o parse do JSON
  DeserializationError erro = deserializeJson(doc, resposta);

  if (erro) {
    Serial.print("[COMANDOS] Erro ao parsear resposta JSON: ");
    Serial.println(erro.c_str());
    return;
  }

  // Verifica se existe o array de comandos de setores
  if (!doc["sector_commands"].is<JsonArray>()) {
    Serial.println("[COMANDOS] Nenhum comando de setor na resposta.");
    return;
  }

  JsonArray comandos = doc["sector_commands"].as<JsonArray>();
  Serial.print("[COMANDOS] Recebidos ");
  Serial.print(comandos.size());
  Serial.println(" comando(s) de setor.");

  // Itera sobre cada comando e aplica a ação
  for (JsonObject cmd : comandos) {
    int sectorId    = cmd["sector_id"] | -1;
    const char* acao = cmd["action"] | "unknown";

    executarComandoSetor(sectorId, acao);
  }

  // Atualiza os LEDs após processar todos os comandos
  atualizarLEDs();
}

// =============================================================================
// BUSCA DE COMANDOS PENDENTES VIA HTTP GET
// =============================================================================
// Faz polling no endpoint /api/commands/pending para buscar comandos
// manuais enviados pelo painel de controle.
// =============================================================================
void buscarComandosPendentes() {
  // Verifica conexão WiFi antes de tentar buscar
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  HTTPClient http;

  // Monta a URL completa
  String url = "http://";
  url += API_HOST;
  url += ":";
  url += API_PORT;
  url += API_COMMANDS_PATH;

  http.begin(url);
  int httpCode = http.GET();

  if (httpCode > 0) {
    if (httpCode == HTTP_CODE_OK) {
      String resposta = http.getString();

      // Só processa se houver conteúdo na resposta
      if (resposta.length() > 2) {
        Serial.print("[POLLING] Comandos pendentes: ");
        Serial.println(resposta);
        processarComandosPendentes(resposta);
      }
    }
  } else {
    Serial.print("[POLLING] Erro ao buscar comandos: ");
    Serial.println(http.errorToString(httpCode));
  }

  http.end();
}

// =============================================================================
// PROCESSAMENTO DE COMANDOS PENDENTES
// =============================================================================
// Espera um JSON no formato:
// {
//   "commands": [
//     {"sector_id": 2, "action": "off"},
//     {"sector_id": 3, "action": "on"}
//   ]
// }
// =============================================================================
void processarComandosPendentes(String resposta) {
  JsonDocument doc;

  DeserializationError erro = deserializeJson(doc, resposta);

  if (erro) {
    Serial.print("[POLLING] Erro ao parsear JSON: ");
    Serial.println(erro.c_str());
    return;
  }

  // Tenta processar como array "commands" (formato do endpoint de polling)
  if (doc["commands"].is<JsonArray>()) {
    JsonArray comandos = doc["commands"].as<JsonArray>();

    Serial.print("[POLLING] Processando ");
    Serial.print(comandos.size());
    Serial.println(" comando(s) pendente(s).");

    for (JsonObject cmd : comandos) {
      int sectorId    = cmd["sector_id"] | -1;
      const char* acao = cmd["action"] | "unknown";

      executarComandoSetor(sectorId, acao);
    }

    // Atualiza os LEDs após processar todos os comandos
    atualizarLEDs();
  }

  // Também tenta processar como "sector_commands" (caso a API use o mesmo formato)
  if (doc["sector_commands"].is<JsonArray>()) {
    processarComandosResposta(resposta);
  }
}

// =============================================================================
// EXECUÇÃO DE COMANDO EM UM SETOR ESPECÍFICO
// =============================================================================
// Recebe o ID do setor e a ação ("on" ou "off") e aplica a mudança.
// =============================================================================
void executarComandoSetor(int sectorId, const char* acao) {
  // Valida o ID do setor (1-4)
  if (sectorId < 1 || sectorId > 4) {
    Serial.print("[COMANDO] ID de setor inválido: ");
    Serial.println(sectorId);
    return;
  }

  // O array é indexado a partir de 0, mas os IDs começam em 1
  int indice = sectorId - 1;

  // Determina o novo estado baseado na ação
  bool novoEstado;
  if (strcmp(acao, "on") == 0) {
    novoEstado = true;
  } else if (strcmp(acao, "off") == 0) {
    novoEstado = false;
  } else {
    Serial.print("[COMANDO] Ação desconhecida: ");
    Serial.println(acao);
    return;
  }

  // Verifica se houve mudança de estado
  if (sectors[indice].active != novoEstado) {
    sectors[indice].active = novoEstado;

    Serial.print("[COMANDO] Setor '");
    Serial.print(sectors[indice].name);
    Serial.print("' -> ");
    Serial.println(novoEstado ? "LIGADO" : "DESLIGADO");

    // Atualiza o LED correspondente imediatamente
    digitalWrite(sectors[indice].ledPin, novoEstado ? HIGH : LOW);
  } else {
    Serial.print("[COMANDO] Setor '");
    Serial.print(sectors[indice].name);
    Serial.print("' já está ");
    Serial.println(novoEstado ? "LIGADO" : "DESLIGADO");
  }
}
