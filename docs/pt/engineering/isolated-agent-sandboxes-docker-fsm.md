---
title: "Ambientes Isolados Para Agentes na Própria Infra: Containers, FSM e Capability Gates"
date: 2026-11-20
tags:
  - agents
  - docker
  - fsm
  - infrastructure
  - scorphionz
---

# Ambientes Isolados Para Agentes na Própria Infra: Containers, FSM e Capability Gates

A discussão recente sobre *"move to cloud agents"* — levantada por [Peter Steinberger no X](https://x.com/steipete/status/2122412909619994984) e esclarecida na sequência da thread ([parte 2](https://x.com/steipete/status/2122455992214671500), [parte 3](https://x.com/steipete/status/2122459368407150806)) — toca em um ponto operacional real: o problema não é rodar inferência local ou em nuvem, mas sim **onde e com qual nível de isolamento o agente executa comandos**.

Na prática de produção, deixar um agente autônomo operar diretamente sobre o sistema operacional do host de trabalho ou sobre infraestrutura compartilhada sem fronteiras rígidas transforma qualquer erro de raciocínio do modelo em dano direto de ambiente.

---

## O Falso Dilema Entre "Local" e "Cloud"

"Cloud agent", do ponto de vista de arquitetura de sistemas, significa **execução isolada e efêmera**, não dependência de provedor terceiro:

- **Inferência pode ser local ou remota:** modelos rodando na própria máquina ou VPS atendem a camada de geração de tokens.
- **Execução precisa de jaula:** o agente que lê arquivos, roda testes e manipula repositórios deve operar dentro de containers dedicados (Docker ou Podman), com filesystem delimitado, rede controlada e variáveis de ambiente estritamente separadas das credenciais do operador.

É exatamente essa separação que adotamos na construção do **Clawler**, do **Hyades** e do **Jataí**: o plano de controle e o sandbox vivem na nossa própria infraestrutura (*Everything is in our own claws*), sem entregar o controle de execução para orquestradores opacos de terceiros.

---

## Três Camadas de Contenção Que Funcionam no Chão de Fábrica

Para evitar que um agente degrade o ambiente ou execute ações fora do escopo, o isolamento de container sozinho não basta — ele precisa trabalhar em conjunto com a camada de orquestração:

1. **Sandbox por Container (Docker / Podman):** cada tarefa ou *minion* executa em um espaço isolado, sem acesso direto a chaves SSH do host, `.env` de produção ou processos irmãos.
2. **Orquestração Determinística por FSM:** o LLM não decide transições de estado nem o fluxo global da aplicação; uma Máquina de Estados Finitos (FSM) controla qual etapa está ativa.
3. **Capability Gates por Estado:** cada nó da FSM expõe apenas as ferramentas mínimas necessárias para aquele passo (por exemplo, leitura de repositório sem permissão de escrita em produção ou *merge*).

---

## Conclusão Operacional

Migrar agentes da máquina principal para containers isolados na própria infraestrutura resolve o risco operacional sem abrir mão de soberania de dados, previsibilidade de custo ou inferência local. O ganho não está no rótulo "cloud", mas na combinação entre isolamento de sistema operacional e controle determinístico de estado.
