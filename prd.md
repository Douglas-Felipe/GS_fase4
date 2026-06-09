# Documento de Requisitos do Produto (PRD) – LunarGrid

## 1. Visão Geral do Produto

O **LunarGrid** é um sistema inteligente de gerenciamento e otimização de malha energética para bases operacionais em ambientes extremos, especificamente focado na Lua. O sistema combina hardware embarcado para coleta e atuação local, inteligência artificial preditiva para antecipação de cenários climáticos/orbitais e uma interface web para monitoramento e simulação de estresse.

O principal diferencial do LunarGrid é sua capacidade de **antecipar transições críticas** (como o ciclo de noite lunar) e coordenar o desligamento preventivo e ordenado de setores da base, garantindo a preservação dos sistemas vitais (Suporte à Vida).

---

## 2. Objetivos Estratégicos e de Negócio

* **Garantir a Sobrevivência da Base:** Evitar o esgotamento total das baterias por meio de um algoritmo de priorização de setores.
* **Eficiência de Banda e Consumo:** Utilizar comunicação intermitente e otimizada (intervalos de ~1 hora) no hardware para simular as restrições reais de comunicação espacial.
* **Previsibilidade Computacional:** Mudar o paradigma de gerenciamento energético de "reativo" (agir após a queda de energia) para "preditivo" (agir antes da escassez).
* **Ambiente de Homologação:** Fornecer aos operadores uma interface rica para simular cenários catastróficos e validar as decisões da IA.

---

## 3. Escopo Técnico e Stack Tecnológica

* **Hardware / IoT:** ESP32 (físico ou simulado via Wokwi).
* **Back-end & API:** Python (FastAPI ou Flask) integrado a bibliotecas de Machine Learning (como Scikit-Learn ou TensorFlow/Keras).
* **Front-end:** React (Web).

---

## 4. Requisitos Funcionais (RF)

### 4.1. Módulo Embarcado (ESP32)

* **RF-001 (Telemetria):** O ESP32 deve coletar dados de geração solar, nível atual da bateria e consumo geral da base.
* **RF-002 (Envio Intermitente):** O envio desses dados para a API em Python deve ocorrer em intervalos médios de 1 hora (ou em frações de tempo menores aceleradas para fins de demonstração da POC).
* **RF-003 (Atuação de Setores):** O ESP32 deve conter relés ou pinos de controle (simulados por LEDs) que representam o estado (Ligado/Desligado) de quatro setores da base:
1. *Suporte à Vida (Prioridade 1 - Crítica)*
2. *Comunicações Base-Terra (Prioridade 2 - Alta)*
3. *Laboratório de Pesquisa (Prioridade 3 - Média)*
4. *Recarga de Rovers / Mineração (Prioridade 4 - Baixa)*


* **RF-004 (Execução de Comandos):** O ESP32 deve escutar ou receber comandos da API em Python para efetuar o desligamento físico/lógico instantâneo dos setores determinados.

### 4.2. Inteligência Artificial (Módulo Preditivo em Python)

* **RF-005 (Análise Multivariável):** O modelo deve processar cinco variáveis de entrada: consumo atual, prioridade de setor, horário lunar (posição orbital), nível da bateria e nível de geração de energia.
* **RF-006 (Predição de Ciclo Orbital):** A IA não deve apenas reagir ao nível baixo de bateria. Ela deve analisar a tendência temporal do horário lunar para prever a chegada iminente da noite lunar (período sem geração solar).
* **RF-007 (Tomada de Decisão Autônoma):** Caso a IA preveja que a carga da bateria não sustentará toda a base durante o próximo período de sombra, ela deve emitir uma ordem de corte imediato para os setores de menor prioridade (ex: Recarga de Rovers e Laboratório), estendendo a autonomia dos setores críticos.

### 4.3. Interface de Controle e Simulação (React)

* **RF-008 (Painel em Tempo Real):** Exibir um dashboard com gráficos de linha e medidores visuais atualizados com a telemetria enviada pelo ESP32.
* **RF-009 (Status dos Setores):** Mostrar visualmente quais setores estão ativos, desligados manualmente ou cortados preventivamente pela IA.
* **RF-010 (Simulador de Estresse):** Fornecer controles (sliders/inputs) na interface para que o usuário force alterações manuais nos dados:
* Zerar ou reduzir drasticamente a Geração Solar (simulando tempestade de poeira ou noite precoce).
* Alterar o nível da bateria.
* Avançar ou retroceder o horário lunar simulado.


* **RF-011 (Sobrescrita de Comandos):** Permitir que o operador envie um comando manual de ativação/desativação de setores para o ESP32, substituindo temporariamente a automação da IA em caso de emergência.

---

## 5. Requisitos Não-Funcionais (RNF)

* **RNF-001 (Arquitetura do Código Python):** A API em Python deve ser estruturada seguindo boas práticas de arquitetura (como separação clara de responsabilidades em camadas), isolando as regras do modelo de Machine Learning dos controladores HTTP/Rotas.
* **RNF-002 (Desempenho da Interface):** A aplicação React deve gerenciar o estado de forma otimizada para evitar travamentos na renderização ao receber atualizações frequentes de telemetria ou dados de simulação.
* **RNF-003 (Persistência leve):** Os dados históricos de telemetria para o treinamento ou validação do modelo devem ser armazenados de forma estruturada (pode ser um banco relacional leve como SQLite ou arquivos estruturados para a POC).
* **RNF-004 (Protocolo de Comunicação):** A comunicação entre o ESP32 e a API Python deve utilizar HTTP (REST) ou MQTT, garantindo payload leve no formato JSON.

---

## 6. Fluxo de Dados e Arquitetura da POC

1. **Geração e Coleta:** O ESP32 mede/calcula as variáveis de energia da base.
2. **Transmissão:** A cada ciclo determinado, o ESP32 dispara um payload JSON via rede para a API Python.
3. **Processamento e Predição:** A API recebe os dados, salva o histórico e alimenta o modelo preditivo. A IA avalia a projeção de consumo versus o horário lunar.
4. **Ação de Controle:** Se a IA detectar risco de colapso nos próximos ciclos, a API responde ao ESP32 (ou envia um comando) especificando quais pinos/setores devem ser desativados.
5. **Visualização:** A aplicação React consome os mesmos endpoints da API para plotar o comportamento em tempo real e permite o envio de dados simulados para testar o comportamento do modelo preditivo em situações anômalas.

---

## 7. Critérios de Aceitação para a Entrega (Global Solution)

* **Validação da IA:** O modelo em Python deve provar em testes (documentados no PDF) que consegue derrubar o setor de menor prioridade *antes* que a bateria atinja o nível crítico, baseando-se no avanço do relógio lunar.
* **Hardware Funcional:** O ESP32 deve refletir visualmente (via pinos, LEDs ou console) a perda de energia de um setor assim que comandado pela IA ou pela interface.
* **Fidelidade do Simulador:** Ao alterar o slider de "Geração Solar" para 0% no React, o sistema deve iniciar o protocolo de contingência de forma perceptível na tela e no hardware em poucos segundos.
* **Formato de Código:** Nenhum trecho de código da API em Python ou do React pode estar em formato de imagem no PDF final da entrega, cumprindo estritamente as regras da coordenação.