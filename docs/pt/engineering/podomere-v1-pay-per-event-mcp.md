---
title: "ScorphionZ Podomere v1: Enriquecimento B2B Pay-Per-Event e Cliente MCP Desacoplado"
date: 2026-11-19
tags:
  - scorphionz
  - podomere
  - mcp
  - fastapi
  - apify
---

# ScorphionZ Podomere v1: Enriquecimento B2B Pay-Per-Event e Cliente MCP Desacoplado

Ferramentas tradicionais de enriquecimento de dados B2B operam sob assinaturas mensais rígidas e retenção opaca de dados. No **ScorphionZ Podomere v1** — publicado na Apify Store em 16/11/2026 — aplicamos a regra central da nossa arquitetura: cobra-se pelo serviço e pela execução server-side bem-sucedida, mantendo o cliente fino aberto e zero retenção de dados.

---

## Separação Entre Cliente MCP e Motor Proprietário

A arquitetura do Podomere divide a superfície de integração do núcleo de execução:

- **Cliente MCP fino (`ScorphionZ/podomere-mcp`):** distribuído sob licença MIT (`uvx podomere-mcp`), expondo as ferramentas para agentes e orquestradores sem carregar lógica proprietária no lado do cliente.
- **Backend proprietário (`api.scorphionz.com/podomere/v1`):** serviço em **FastAPI** responsável pela coleta *logged-off* em URLs públicas e detecção de *tech stack*, sem coleta de PII pessoal e com política estrita de *Zero Data Retention*.
- **Actor na Apify Store:** empacotamento voltado a automações em **n8n**, **Make** e pipelines de prospecção sob demanda.

---

## Modelo Econômico Pay-Per-Event (PPE)

Em vez de cobrar por execução falhada ou assinatura ociosa, o arquivo `.actor/pay_per_event.json` define dois eventos objetivos de cobrança:

1. `apify-actor-start`: **$0,005** por inicialização do Actor.
2. `domain_enriched`: **$0,01** por domínio enriquecido, disparado via `Actor.charge()` **exclusivamente quando a resposta HTTP retorna 200** com extração válida.

Após a taxa de 20% da plataforma e o consumo de *Compute Units*, o modelo mantém margem líquida próxima de **79,4%** por execução válida, alinhando custo operacional diretamente à entrega útil.

Para integrações *machine-to-machine* diretas na API sem intermediário da Apify Store, o endpoint também suporta liquidação via protocolo **x402** ($0,02 USDC por chamada em Base/Solana).

---

## Integração Direta em Workflows (n8n, Make e MCP)

O desacoplamento permite plugar o mesmo motor em dois fluxos distintos:

- **Automação low-code (n8n / Make):** disparo do Actor na Apify Store recebendo lista de domínios públicos e retornando o JSON de stack e sinais técnicos sem contrato mensal.
- **Agentes autônomos (MCP):** execução direta via `uvx podomere-mcp`, permitindo que agentes consultem a infraestrutura pública de um alvo antes de montar qualquer diagnóstico técnico.

*Everything is in our own claws.*
