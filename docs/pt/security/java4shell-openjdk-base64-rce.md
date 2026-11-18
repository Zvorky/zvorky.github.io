---
title: "Java4Shell (CVE-2026-114938): Quando Intrinsics AVX-512 Reintroduzem Corrupção de Memória na JVM"
date: 2026-11-18
tags:
  - security
  - jvm
  - x86-64
  - avx-512
  - memory-corruption
---

# Java4Shell (CVE-2026-114938): Quando Intrinsics AVX-512 Reintroduzem Corrupção de Memória na JVM

A premissa de segurança de memória da JVM vale até o ponto em que o compilador JIT (C2) substitui código Java gerenciado por *intrinsics* em assembly manual. A divulgação do [Java4Shell (CVE-2026-114938)](https://calif.io/java4shell/) pelos pesquisadores da Calif — corrigida pelo [OpenJDK Vulnerability Advisory de 17/11/2026](https://openjdk.org/groups/vulnerability/advisories/2026-11-17) — expõe exatamente essa fronteira: um *out-of-bounds write* no decoder Base64 x86-64 do HotSpot que permite vazamento de heap e execução remota de código (RCE).

Sob CVSS 4.0, a falha recebeu pontuação **9.2 (Critical)** (e **8.1** na matriz CVSS v3.1 do OpenJDK para o componente `hotspot/compiler`).

---

## O Mecanismo da Falha: Underflow na Máscara `evmovdqub`

Para acelerar a decodificação Base64 em processadores x86-64 com suporte a **AVX-512 VBMI**, o HotSpot utiliza um *stub* em assembly que processa blocos de 256 bytes e, no restante menor que 64 bytes, recorre à instrução `evmovdqub` (`VMOVDQU8`) com uma máscara de 64 bits (`k1`).

O erro ocorre no cálculo da máscara de saída (*output mask*) quando o bloco residual contém apenas *padding* (`=`, `==`, `X=`, `X==`, `XY=` ou `===`):

1. Para uma entrada de 65 bytes (`"A" * 64 + "="`, ou `"A" * 128 + "="` no OpenJDK 17 devido ao limiar maior do caminho rápido), o runtime aloca um buffer de saída de **50 bytes**.
2. Após decodificar os primeiros 64 bytes, o cálculo residual de `output_len` parte de zero e é decrementado ao detectar `=`.
3. O *underflow* resultante (`-1` ou `-2`) faz com que `bzhiq(-1, output_len)` não zere nenhum bit (`output_len >= 64` em aritmética sem sinal).
4. A máscara `k1` assume `0xFFFFFFFFFFFFFFFF` (`-1u64`).
5. A instrução `evmovdqub` escreve **64 bytes completos** a partir do offset 48, gravando **62 bytes fora dos limites** do array alocado (offsets 50 a 111) antes que a camada Java lance `IllegalArgumentException`.

---

## De Escrita Fixa a Heap Leak e RCE

Embora os bytes gravados fora dos limites tenham conteúdo fixo (incluindo `0x9a` nos offsets 48..63 do bloco escrito), a posição de aterrissagem na heap G1 é controlável via *Heap Feng Shui* remoto:

- **Grooming de TLAB e regiões G1:** requisições HTTP mantidas abertas antes do envio do sufixo (sincronizadas por TCP ACK) posicionam arrays vizinhos (`writer` e `reader`) fora dos TLABs locais de thread.
- **Writer / Reader primitives:** ao sobrescrever o campo de comprimento de um array adjacente (`writer`), o atacante transforma a escrita fixa em escrita linear limitada de valores arbitrários, corrompendo um segundo array (`reader`) para vazar memória da heap (chaves, tokens, PII) e reparar objetos danificados antes de atingir hooks da JVM e o Code Cache.

Distribuições OpenJDK **17.0.6+** e builds derivados (Corretto, Temurin, Zulu, Liberica, SapMachine, Red Hat, Oracle JDK/GraalVM) em hosts **x86-64 com AVX-512 VBMI** (Intel Xeon Ice Lake+, AMD EPYC/Ryzen Zen 4+) são afetados. Hosts **ARM64 não são afetados**.

---

## Diagnóstico Rápido e Mitigação Imediata

Para verificar se um host Linux x86-64 possui as flags de CPU exigidas pelo *intrinsic* vulnerável:

```bash
grep -m1 '^flags' /proc/cpuinfo | tr ' ' '\n' | grep -E '^(avx512f|avx512bw|avx512vbmi|bmi2)$'
```

Se todas as quatro flags (`avx512f`, `avx512bw`, `avx512vbmi`, `bmi2`) aparecerem na saída:

1. **Ação definitiva:** atualizar o runtime OpenJDK / Oracle Java para os patches publicados em **17/11/2026** (correções aplicadas para as séries 8, 17, 21, 25 e 27 conforme o advisory oficial).
2. **Mitigação temporária (hosts x86-64 sem patch imediato):** desabilitar o *intrinsic* Base64 ou o uso de AVX-512 nos argumentos da JVM:

```bash
# Desabilita apenas o intrinsic de Base64 (preferível)
java -XX:-UseBASE64Intrinsics -jar app.jar

# Alternativa: restringe o conjunto de instruções para AVX2
java -XX:UseAVX=2 -jar app.jar
```

> **Atenção:** não aplique `-XX:-UseBASE64Intrinsics` ou `-XX:UseAVX=2` em hosts ARM64, pois a JVM rejeitará a flag na inicialização.

---

## Lição Estrutural

Otimizações em assembly escritas à mão para ganhar throughput em operações banais (como decodificação Base64) ampliam a superfície de corrupção de memória para toda aplicação que consome o runtime — mesmo serviços que decodificam payloads de poucas dezenas de bytes. Em infraestrutura própria (*Everything is in our own claws*), auditar e desativar *intrinsics* desnecessários ou manter inventário exato de flags de CPU por nó reduz o raio de impacto antes mesmo da chegada do patch.
