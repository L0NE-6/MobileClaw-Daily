<div align="center">

# 🦞 MobileClaw Daily

**Benefício diário de tokens MobileClaw · várias contas · status → claim → status / credits**

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

<img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" />

</div>

> [!IMPORTANT]
> Este projeto é gratuito. É proibido revender, colocar atrás de pagamento,
> cobrar por implantação, redistribuir para captação, fingir ser o autor ou
> remover avisos de copyright. Consulte [NOTICE.md](../NOTICE.md).

## Função

MobileClaw Daily é um projeto independente mantido originalmente pela L0NE-6.
Ele verifica a atividade `1003`, executa o claim quando disponível e confirma o
resultado pelo status e pelo saldo de credits no servidor.

| Item | Descrição |
| :--- | :--- |
| Entrada | `MOBILECLAW_TOKENS` ou `MOBILECLAW_TOKEN` |
| Saída | JSON por conta e um JSON final de resumo |
| Ambiente | Python 3.9+ com `requests` |
| Implantação | Windows, Linux, Qinglong, GitHub Actions |
| Sucesso | Estado final ou recibo de claim confirmado e credits legíveis |

## Fluxo do Protocolo

```text
POST status {"activityCodes":["1003"]}
  ├─ claimed   -> GET credits -> ALREADY_CLAIMED
  └─ claimable -> POST claim {"activityCode":"1003"}
                    -> POST status again
                    -> GET credits
                    -> CLAIMED / CLAIM_NOT_APPLIED / READBACK_UNCONFIRMED
```

HTTP 200 isolado não é sucesso. O resultado precisa de um estado final
confiável ou recibo de claim, além da leitura de credits.

## Credenciais

`MOBILECLAW_TOKENS` aceita vírgula ou quebra de linha:

```text
Bearer <token>
Authorization: <token>
Cookie: <name>=<value>; <name>=<value>
<token>
```

Valor sem `=` é tratado como Bearer Token. Valor com `=` é tratado como Cookie.
`MOBILECLAW_TOKEN` só é usado quando `MOBILECLAW_TOKENS` está vazio.

Nunca envie tokens, cookies, telefones, arquivos de autenticação ou relatórios
reais para o repositório.

## Erros de Elegibilidade

| Código | Significado |
| :--- | :--- |
| `C404003` | Conta não registrada |
| `C403001` | Verificação de identidade incompleta |
| `C401003` | Verificação de identidade em análise |

Esses casos retornam `INELIGIBLE`. Conclua a etapa necessária na conta antes de
executar novamente.

## Execução Local

```bash
python -m pip install -r requirements.txt
export MOBILECLAW_TOKEN='<seu token ou cookie>'
python mobileclaw_daily.py
```

Somente status:

```bash
python mobileclaw_daily.py --status
```

## Qinglong

1. Instale `requests`.
2. Envie `mobileclaw_daily.py`.
3. Configure `MOBILECLAW_TOKENS` ou `MOBILECLAW_TOKEN`.
4. Crie uma tarefa com `task mobileclaw_daily.py`.
5. Execute uma vez por dia conforme a regra da conta.

## GitHub Actions

O workflow executa testes em cada push para `main`. Uma execução diária agenda
testes, claim e upload do relatório JSON como artifact.
Sem um Secret de credenciais configurado, o claim agendado é ignorado com um notice SKIPPED explícito; depois que as credenciais existirem, falhas do script continuam sendo falhas.

| Secret | Obrigatório | Valor |
| :--- | :---: | :--- |
| `MOBILECLAW_TOKENS` | Um dos dois | Tokens ou cookies de várias contas |
| `MOBILECLAW_TOKEN` | Um dos dois | Token ou cookie de uma conta |

O cron é `17 23 * * *` UTC, 07:17 no horário de Pequim. O agendamento do
GitHub pode atrasar.

## Critérios de Sucesso

- `ALREADY_CLAIMED`: status `claimed` e credits legíveis.
- `CLAIMED`: status final `claimed`, ou recibo de claim `claimed` com o atraso
  final registrado, e credits legíveis.
- `AVAILABLE`: modo de consulta confirma `claimable` e lê credits.
- `CLAIM_NOT_APPLIED`, `READBACK_UNCONFIRMED` e `STATUS_UNRECOGNIZED` são falhas.

## Testes

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check mobileclaw_daily.py tests
```

Os testes usam fake sessions e não acessam o serviço real.

## Privacidade

O repositório não armazena credenciais nem dados pessoais. As saídas são
mascaradas e os relatórios gerados são ignorados pelo Git.

## Aviso

Use apenas para automação pessoal lícita. Regras, elegibilidade, interfaces e
saldos são controlados pelo provedor do serviço. O uso é por sua conta e risco.

---

[Voltar ao README chinês](../README.md) · [Política de uso](../NOTICE.md) · [Doação e Star History](../README.md#star-trail)
