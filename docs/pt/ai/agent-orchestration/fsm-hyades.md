---
title: Engenharia de Sistemas para Agentes de IA - Por que Loops Estocásticos Quebram em Produção e como FSMs e Minions Resolvem o Problema
description: Um mergulho na arquitetura determinística do Hyades, decomposição em minions inspirada no Starnet e controle estrito de memória e estado.
date: 2026-10-08
tags:
  - IA
  - Agentes
  - FSM
  - Hyades
  - Starnet
  - Arquitetura de Sistemas
  - Linux
---

# Engenharia de Sistemas para Agentes de IA: Por que Loops Estocásticos Quebram em Produção e como FSMs e Minions Resolvem o Problema

> **Status do Projeto:** WIP / Em desenvolvimento ativo  
> **Autor:** Enzo Zavorski Delevatti ([@Zvorky](https://github.com/Zvorky))  
> **Data:** Outubro de 2026  
> **Tópicos:** Engenharia de Sistemas, Agentes Autônomos, Máquinas de Estados Finitos (FSM), Linux IPC, Model Context Protocol.

---

A indústria de software está vivendo uma ressaca previsível com agentes de IA. 

Entre 2023 e 2025, o ecossistema foi inundado por frameworks que prometiam autonomia total através de abstrações em camadas altíssimas sobre chamadas de LLM. Bastava instanciar um agente, plugar cinco ferramentas, escrever um *system prompt* empolgado e deixá-lo "pensar".

Em demonstrações controladas de três minutos, tudo parece mágico. Mas o choque de realidade ao colocar essas soluções em produção é brutal: **entre 40% e 60% das execuções de fluxos agênticos corporativos falham**.

As falhas raramente decorrem da inteligência do modelo de linguagem em si. O gargalo é puramente de **engenharia de sistemas**: tentou-se delegar o **plano de controle da aplicação** a um processo probabilístico.

Neste artigo, discuto por que os loops abertos tradicionais colapsam, como o conceito de **minions** explorado pelo [Starnet (androoAGI)](https://github.com/androoAGI/starnet) aponta para a decomposição correta e como venho construindo o **Hyades** — um orquestrador determinístico focado estritamente na função e na blindagem de recursos, e não em estética superficial.

---

## 1. O Problema Fundamental: O "Von Neumann Semântico" e o Loop ReAct Aberto

Na arquitetura clássica de computadores de Von Neumann, instruções de controle e dados trafegam pelo mesmo barramento físico de memória — a raiz histórica de vulnerabilidades como *Buffer Overflow* e *SQL Injection*. 

Nos modelos de linguagem contemporâneos baseados em Transformers, sofremos de uma variação semântica desse mesmo dilema: **dentro da janela de contexto, instruções do operador e dados externos não-confiáveis compartilham o mesmo espaço de atenção.** Não existe um *Ring 0* nativo de hardware na camada de tokens.

Quando frameworks populares (como LangChain, CrewAI ou AutoGen) implementam o padrão ReAct (*Reason + Act*), eles tratam o ciclo de vida do agente como um loop *while* aberto:

```
[Entrada do Usuário] 
       │
       ▼
┌───────────────────────────────┐
│     Prompt com N Ferramentas  │ ◄──────────┐
└──────────────┬────────────────┘            │
               │                             │
               ▼                             │ (Loop Estocástico)
┌───────────────────────────────┐            │
│  LLM Decide Próximo Passo     │ ───────────┘
│  (e decide quando parar)      │
└──────────────┬────────────────┘
               │
               ▼
[Resultado ou Colapso do Fluxo]
```

Se o modelo decide **o que fazer**, **qual ferramenta chamar** e **quando a tarefa foi concluída**, você introduz três pontos de quebra inevitáveis:

1. **Ausência de Determinismo no Controle de Fluxo:** Uma variação de temperatura ou uma resposta inesperada de uma API externa faz o modelo pular validações de negócio e transicionar prematuramente para a finalização.
2. **Alucinação de Tool-Calling por Sobrecarga de Contexto:** Ao expor 10 ou 20 ferramentas simultaneamente no contexto, a probabilidade do modelo invocar a ferramenta errada — ou invocá-la fora de ordem cronológica — cresce exponencialmente.
3. **Transbordamento de Contexto (*Context Bleed*):** O histórico de tentativas falhas, mensagens de erro e alucinações intermediárias vai poluindo a janela de contexto. O modelo passa a prestar atenção nos próprios erros passados, entrando em loops de repetição que drenam o orçamento de tokens.

Para que um sistema autônomo seja confiável em produção, a regra fundamental de sistemas distribuídos precisa ser restabelecida: **o LLM nunca deve governar o fluxo de controle da aplicação.**

---

## 2. A Morte do Agente Monolítico: O Conceito de Minions

Um dos projetos mais instigantes que estudei recentemente é o [**Starnet**](https://github.com/androoAGI/starnet), desenvolvido pelo androoAGI. 

O Starnet ataca com precisão a falácia do "agente monolítico". Em vez de conceber um único agente gigante que lê o objetivo, decompõe o problema, chama dezenas de ferramentas, avalia o resultado e gera a resposta, ele propõe a segregação em **minions**.

Um *minion* é um sub-agente:
* **Descartável:** Possui ciclo de vida efêmero, instanciado apenas para resolver uma subtarefa atômica.
* **Escopo Cirúrgico:** Recebe exclusivamente o contexto estritamente necessário para aquele passo (minimizando o *context bleed*).
* **Isolado:** Não compartilha estado volátil diretamente com outros minions; o resultado é devolvido de forma estruturada.

No entanto, mesmo a divisão em minions se torna caótica se a coordenação entre eles for governada por outro loop probabilístico. Se o "gerente" dos minions for outra LLM decidindo no improviso quem chamar a seguir, você apenas distribuiu o caos estocástico em múltiplos processos.

A peça que falta para fechar essa equação é a **Máquina de Estados Finitos (FSM)**.

---

## 3. A Solução Arquitetural: FSM Determinística + Capability Gates

A abordagem que transforma esse cenário em engenharia de produção é inverter a hierarquia de controle. O software determinístico governa; o modelo apenas computa.

```
                  ┌─────────────────────────────────────────┐
                  │    FSM Determinística (Código Rígido)   │
                  │   Estados Válidos e Contratos Estritos   │
                  └────────────────────┬────────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
┌───────────────┐              ┌───────────────┐              ┌───────────────┐
│ Estado: PARSE │              │ Estado: EVAL  │              │ Estado: EXEC  │
├───────────────┤              ├───────────────┤              ├───────────────┤
│ Capability:   │              │ Capability:   │              │ Capability:   │
│ [read_spec]   │              │ [calc_diff]   │              │ [write_db]    │
└───────┬───────┘              └───────┬───────┘              └───────┬───────┘
        │                              │                              │
        ▼                              ▼                              ▼
   (Minion LLM                    (Minion LLM                    (Minion LLM
    Escopo Puro)                   Escopo Puro)                   Escopo Puro)
```

Essa arquitetura se apoia em três pilares:

### 1. Transição de Estado por Código Estrito
A esteira de execução é modelada como um grafo acíclico direcionado (DAG) ou uma FSM com transições explícitas:
$$\text{Estado}_{n+1} = \delta(\text{Estado}_n, \text{Evento Validado})$$

O LLM é invocado *dentro* de um estado para processar uma transformação textual ou estruturada (ex: extrair dados, gerar código, sumarizar). Uma vez retornada a saída, um validador de schema (ex: Pydantic) checa os tipos. Se a saída for válida, o **código** dispara o evento que transiciona para o próximo estado. O modelo sequer sabe qual é o estado seguinte.

### 2. Capability Gates Dinâmicos
Em sistemas operacionais, o kernel isola instruções privilegiadas via anéis de proteção (*Ring 0* vs *Ring 3*). Em agentes de IA, esse princípio se traduz em **Capability Gates**.

Cada estado da FSM injeta no contexto **exclusivamente as ferramentas permitidas para aquele momento**:
* No estado de leitura e análise (`ANALYZING`), ferramentas que possuem efeitos colaterais (gravação em banco, envio de e-mails, execução de comandos bash) **simplesmente não existem** na lista de schemas enviada ao modelo.
* Mesmo que o agente sofra uma tentativa de *Prompt Injection Indireto* através de um documento malicioso, a injeção falha por ausência física de ferramentas destrutivas disponíveis naquele estado.

### 3. Persistência Atômica Local
Em vez de depender de arrays efêmeros na memória do processo, cada transição de estado, meta de sessão e transcrição deve ser gravada transacionalmente (utilizando padrões como SQLite em modo WAL). Isso permite congelar o processo, inspecionar o histórico e retomar execuções sem perda de estado.

---

## 4. Por Dentro do Hyades: Construindo a Sala de Máquinas

O **Hyades** é o projeto onde venho implementando esses conceitos na prática. 

Desde o primeiro commit, adotei uma diretriz clara: **priorizar 100% a função sobre a estética**. Antes de desenhar interfaces bonitas ou telas com gradientes, a "sala de máquinas" — o modelo de processos, a máquina de estados, a gestão de memória e a integridade de dados — precisa ser inabalável.

Abaixo destaco os principais componentes arquiteturais já desenvolvidos e testados no repositório:

### 4.1. Core FSM Desacoplado e Contratos de Transição
O coração do Hyades é um motor de FSM desacoplado das interfaces de entrada. Cada estado possui contratos invariantes:
* Schemas estritos de entrada e saída.
* Capability Gates declarativos que filtram ferramentas em tempo de execução.
* Tratamento atômico de exceções com fallback determinístico de recuperação de erro.

### 4.2. Arquitetura de Daemon de Background com IPC Dedicado
Em vez de rodar como um script monolítico que bloqueia o terminal, o Hyades opera com um modelo de **processo daemon independente** (`hyades-daemon`).
* O daemon gerencia o ciclo de vida das sessões, a esteira de eventos e a comunicação com os modelos.
* As interfaces de controle (seja uma CLI rápida, uma interface de terminal ou um cockpit web) conectam-se ao daemon através de um protocolo IPC leve, assíncrono e desacoplado.

### 4.3. Auditoria de Recursos de Baixo Nível: VmRSS via `/proc`
Muitos frameworks em Python sofrem de vazamento silencioso de memória que só é percebido quando o OOM-Killer do Linux derruba o contêiner em produção.

No Hyades, a suíte de qualidade audita o consumo de memória real do processo inspecionando diretamente as métricas de `VmRSS` (Virtual Memory Resident Set Size) em `/proc/[pid]/status`:
* Evita a distorção de medições infladas por `fork()` sob execução concorrente de testes.
* Estabelece limites estritos de footprint de memória em repouso e sob carga contínua.

### 4.4. Mascaramento e Redação de Segredos em Nível de Payload
Um dos maiores riscos ao persistir transcrições completas de agentes é o vazamento inadvertido de chaves de API, tokens `sk-` e senhas para arquivos de log ou telas de visualização.

Implementamos um interceptador de eventos que atua diretamente na camada de payload:
* Campos sensíveis conhecidos são substituídos por máscaras de segurança.
* Strings livres passam por filtros de expressão regular antes de serem persistidas no histórico ou transmitidas via websocket para a interface.

### 4.5. Interfaces Operacionais: Textual TUI, CLI e Starlette Bridge
Para quem opera sistemas, a interface mais rápida é o terminal:
* **CLI Rápida:** Comandos para disparo direto de metas de sessão e consulta de estado.
* **TUI (Terminal User Interface):** Interface reativa de terminal construída em Python com **Textual**, permitindo acompanhar logs, estados da FSM e sessões em tempo real diretamente via SSH.
* **Bridge Web Starlette:** Uma camada de bridge assíncrona expondo rotas protegidas por CSRF para conexão com a interface gráfica (React SPA).

---

## 5. Comparativo Arquitetural: Loop Aberto vs. FSM Governança

| Dimensão Sistêmica | Frameworks Tradicionais (ReAct / Loop Livre) | Arquitetura FSM Governança (Hyades) |
| :--- | :--- | :--- |
| **Controle de Fluxo** | Estocástico (decidido pelo modelo) | Determinístico (código rígido) |
| **Exposição de Tools** | Estática (todas as tools no prompt) | Dinâmica (Capability Gates por estado) |
| **Resiliência a Injeção** | Baixa (vulnerável a desvios de prompt) | Alta (ausência física de tools perigosas) |
| **Persistência de Estado** | Efêmera / In-memory | Transacional (SQLite WAL auditável) |
| **Depuração / Rollback** | Caixa-preta imprevisível | Transições rastreáveis estado a estado |
| **Pegada de Recursos** | Descontrolada (inchaço de contexto) | Auditada (limites de VmRSS e memória) |

---

## 6. Status Atual e Próximos Passos (Living Document)

O Hyades permanece em **desenvolvimento ativo e fechado**. 

Minha prioridade neste momento é estabilizar a esteira de CI, consolidar os quality gates de lint/formatação e garantir que as invariantes de memória e determinismo permaneçam 100% herméticas sob testes pesados de estresse.

Este artigo é um **documento vivo**. À medida que eu avançar nos próximos marcos de desenvolvimento — especialmente nos benchmarks comparativos de throughput, na evolução do protocolo IPC e na integração com provedores locais de inferência —, atualizarei este texto com métricas e detalhes adicionais de implementação.

Assim que a fundação estiver verdadeiramente estável e validada em batalha, o repositório terá seu código-fonte aberto para a comunidade.

---

*Gostou da discussão ou tem uma visão diferente sobre orquestração de agentes? Sinta-se à vontade para abrir uma issue ou trocar uma ideia técnica no meu perfil do GitHub: [@Zvorky](https://github.com/Zvorky).*
