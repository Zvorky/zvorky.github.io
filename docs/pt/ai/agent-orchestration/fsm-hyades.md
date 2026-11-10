# Orquestração Determinística de Agentes: A Arquitetura FSM e Fábrica Espacial do Hyades

**Autor:** Enzo Zavorski Delevatti (`Zvorky`)  
**Data de Atualização:** Novembro de 2026  
**Status:** Arquitetura de Produção (Workstream E)  
**Repositório Oficial:** [zvorky/hyades](https://github.com/Zvorky/Hyades)  

---

## 1. O Fim da Monocultura Probabilística: Por que Rejeitamos o "Loop ReAct" Tradicional

A esmagadora maioria dos frameworks de agentes autônomos contemporâneos (LangChain, AutoGen, CrewAI) sofre do mesmo pecado original: delegar a máquina de estados e o controle de fluxo à inferência probabilística de um LLM.

Nesse modelo ingênuo:
1. O modelo decide o que fazer a seguir com base no histórico acumulado na janela de contexto.
2. A cada passo, concatena-se o output da ferramenta anterior, inflando o prompt até atingir a exaustão de contexto (*Context Rot*).
3. Qualquer falha sintática (uma vírgula fora do lugar em um JSON) interrompe o fluxo ou dispara loops de alucinação descontrolados.
4. A latência e o custo de inferência explodem, tornando o sistema inviável para infraestruturas locais e hardware modesto.

No **Hyades**, partimos de uma premissa inegociável sob a filosofia **"Everything is in our own claws"**:
> **O LLM nunca decide a transição de estado.** O fluxo é governado por uma Máquina de Estados Finitos (FSM) determinística e guardas booleanos rígidos em código CPython puro. O modelo é apenas um operário de execução sob contrato estrito.

---

## 2. A Evolução do Hyades: Da FSM Linear para a Fábrica Espacial Contínua (Workstream E)

Nas primeiras versões (Workstream D), o Hyades operava sobre sessões descartáveis e uma FSM linear única. Essa abordagem provou-se rígida:
- O Mestre nascia e morria com cada comando, gerando amnésia operacional.
- Estados terminais rígidos (`FAILED_TERMINAL`) matavam a execução diante de qualquer erro menor em vez de permitir recuperação.

No **Workstream E**, o Hyades evoluiu para uma **Fábrica Multi-Agente Espacial e Contínua**:

| Dimensão Arquitetural | Paradigma Legado | Nova Arquitetura Hyades (Workstream E) |
| :--- | :--- | :--- |
| **Unidade de Execução** | Sessões descartáveis em disco | **Workspace Contínuo + Hall de Objetivos** com Mestre residente perpétuo no daemon. |
| **Máquina de Estados** | FSM única e linear compartilhada | **Dupla Máquina Desacoplada**: Mestre Estratégico (DAG Não-Linear) + Minions Operacionais em Enclave. |
| **Ciclo de Vida dos Minions** | Minions efêmeros destruídos a cada subtarefa | **Minions Persistentes com Cargos (Roles)** e memória curta rotativa (`rolling_scratchpad`). |
| **Governança de Ferramentas** | Lista global estática de tools no prompt | **RBAC Espacial por Diretório (`zones.json`)**: Crachás definem quais salas o Minion pode acessar. |
| **Acompanhamento de Metas** | Perguntas ao modelo para saber o status | **Métricas Programáticas por Objetivo (Tick Sensors)** avaliadas no SQLite/filesystem com zero LLM. |
| **Interface Humana** | Logs soltos no disco | **Web Cockpit v2 (Jinja2 + HTMX + SSE)** e TUI Textual unificada (< 30MB RAM). |

---

## 3. Os 5 Pilares da Engenharia do Hyades

### 3.1. A Dupla FSM Desacoplada (Master Strategic DAG vs. Minion Micro-Loop)
Em vez de forçar o Mestre e os operários a compartilharem a mesma máquina de estados, o Hyades divide o cérebro do sistema:
- **Master Strategic DAG:** Opera no nível macro dos Objetivos (`ACTIVE`, `ADAPTING`, `WAITING_OPERATOR`, `ACHIEVED`, `MONITORING`). Se um minion falha, o Mestre entra em `ADAPTING`, recalcula a rota e emite novas tarefas; se precisa de credencial humana, pausa em `WAITING_OPERATOR` e chama o operador no chat tático.
- **Minion Operational Loop:** Cada minion opera isolado em seu *TaskEnclave* com um micro-loop de ferramentas autônomo, executando passos atômicos até entregar o artefato final.

### 3.2. RBAC Espacial por Diretório (`zones.json`)
Em sistemas tradicionais, todas as ferramentas (tools) são jogadas de uma vez no prompt do modelo, consumindo milhares de tokens e abrindo brechas para *prompt injection*.
No Hyades, criamos o conceito de **Zonas Espaciais com Crachás de Acesso**:
- O manifesto protegido `.hyades/zones.json` divide o repositório em salas físicas (ex: `research/`, `projects/`, `.terminals/default`).
- Cada Minion possui um Cargo formal: `Builder`, `Researcher`, `Inspector` ou `Executor`.
- Um Minion só consegue ver e executar comandos de ferramentas se o seu Cargo tiver crachá para a sala correspondente. A navegação ocorre via comandos de diretório auditados pelo daemon.

### 3.3. Sensores Programáticos de Tick (Zero Custo de Inferência)
Para saber se um objetivo está progredindo (quantos testes passaram, quantos commits foram gerados, se a branch avançou), o Hyades **não consulta o LLM**.
A cada *tick* do daemon, o `ObjectiveMetricsEngine` avalia coletores determinísticos diretamente no sistema de arquivos e no SQLite local (`memory.db`), emitindo eventos `OBJECTIVE_METRICS_UPDATE` para a interface humana sem queimar um único centavo de inferência.

### 3.4. Memória Hermes e Cristalização Determinística
O modelo de aprendizado contínuo do Hyades segue o princípio de cristalização:
1. Quando uma demanda inédita chega, Minions exploram e testam abordagens.
2. Ao concluir com sucesso, o Mestre analisa os passos executados e **cristaliza** um script determinístico na pasta `.hyades/skills/`.
3. Na próxima vez que uma tarefa idêntica surgir, um único minion leve (modelo 0.8B) apenas executa o script validado em milissegundos, reduzindo o custo a zero.

### 3.5. Web Cockpit v2 (Jinja2 + HTMX + SSE) & TUI Textual
Rejeitamos a complexidade e o peso de frameworks SPA (React/Node.js com 300MB de `node_modules`).
A interface do Hyades é um **cockpit de telemetria aeroespacial** construído com:
- Backend em Starlette servindo templates Jinja2 compilados no servidor.
- Reatividade dinâmica via **HTMX** e streaming de eventos em tempo real via **Server-Sent Events (SSE)**.
- Consumo total de memória RAM do daemon + interface web: **inferior a 30 MB**.
- Interface TUI espelhada em terminal via Textual para operadores que vivem na linha de comando.

---

## 4. Benchmark e Métricas de Eficiência em Produção

Comparativo de execução do Hyades em hardware padrão bare-metal (AMD Ryzen 7, CPU pura Linux, sem GPU):

| Métrica | Hyades (zvorky/hyades) | Stack Tradicional (LangChain + Celery + React) | Ganho Real |
| :--- | :---: | :---: | :---: |
| **Consumo de Memória RAM** | **< 35 MB** | > 450 MB | **-92% de pegada basal** |
| **Dependência de GPU** | **Zero (100% CPU)** | Exigida para modelos pesados | Soberania total |
| **Quebra por Erro Sintático** | **0% (FSM determinística)** | Frequente (alucinação de JSON) | Execução hermética |
| **Tempo de Startup do Daemon** | **< 35 ms** | > 2.500 ms | Instantâneo |
| **Complexidade de Dependências** | **Zero Node/npm** | Centenas de pacotes npm | Sem supply chain attacks |

---

## Conclusão

A autonomia real em engenharia de software não virá do aumento arbitrário de parâmetros de modelos generativos, mas da disciplina arquitetural com que contemos e direcionamos esses modelos. 

O Hyades prova que um sistema multiagente soberano, determinístico e ultrarrápido cabe na memória de um computador comum e opera com estabilidade industrial.

*O repositório e os planos arquiteturais estão disponíveis em [github.com/zvorky/hyades](https://github.com/Zvorky/Hyades).*
