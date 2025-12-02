# ⚡ Guia Rápido - Integração Jira

## 🎯 Resumo em 3 Passos

### 1️⃣ Configurar Webhook no Jira (5 minutos)

**Acesse:** Jira → Configurações → Sistema → WebHooks → Criar WebHook

**Configure:**
```
Nome: Safe2Go - Sincronização de Casos
URL: https://check-funcionando.preview.emergentagent.com/api/webhooks/jira
Eventos: Issue Created, Issue Updated, Issue Assigned
Status: Ativado ✅
```

**Cabeçalho de Segurança:**
```
Nome: X-Webhook-Secret
Valor: safe2go-webhook-secret-2025
```

### 2️⃣ Testar no Jira

1. Clique em **Testar** no webhook criado
2. Selecione **Issue Created**
3. Clique em **Enviar**

**✅ Sucesso:** 
```json
{"status": "created", "case_id": "S2GSS-XXXXX"}
```

### 3️⃣ Criar um Caso Real

1. Crie um novo caso no Jira
2. Aguarde 2-3 segundos
3. Acesse Safe2Go: https://check-funcionando.preview.emergentagent.com/
4. Vá em **Casos**
5. 🎉 **Seu caso apareceu automaticamente!**

---

## 🔄 Como Funciona

```
┌──────────┐         ┌────────────┐         ┌──────────────┐
│   JIRA   │ ──────> │  WEBHOOK   │ ──────> │  SAFE2GO     │
│          │ HTTP    │  ENDPOINT  │ JSON    │  MONGODB     │
│ (Cria)   │ POST    │            │ Salva   │  (Banco)     │
└──────────┘         └────────────┘         └──────────────┘
```

**O que acontece:**
1. 📝 Você cria/edita um caso no Jira
2. 🚀 Jira envia automaticamente para Safe2Go
3. 💾 Safe2Go salva no banco de dados
4. ✅ Caso aparece instantaneamente no sistema

---

## 📋 Campos Sincronizados

| Jira | Safe2Go |
|------|---------|
| ID do Caso (S2GSS-XXXX) | ✅ Jira ID |
| Título (Summary) | ✅ Título |
| Descrição | ✅ Descrição |
| Responsável (Assignee) | ✅ Responsável |
| Status | ✅ Status (mapeado) |

---

## 🏷️ Mapeamento de Status

| Status Jira | Status Safe2Go |
|-------------|----------------|
| To Do | Pendente |
| In Progress | Pendente |
| Done | Concluído |
| Aguardando Cliente | Aguardando resposta do cliente |

---

## ✅ Casos de Uso

### ✨ Criação Automática
```
Jira: Criar caso S2GSS-10700
      ↓
Safe2Go: Caso aparece automaticamente em 2 segundos
```

### 🔄 Atualização Automática
```
Jira: Mudar status para "Done"
      ↓
Safe2Go: Status atualizado para "Concluído"
```

### 👤 Atribuição Automática
```
Jira: Atribuir para "João Silva"
      ↓
Safe2Go: Responsável atualizado para "João Silva"
```

---

## 🚨 Solução Rápida de Problemas

### ❌ Webhook não funciona

**Verifique:**
1. ✅ Webhook está **Ativado** no Jira?
2. ✅ URL está correta?
3. ✅ Cabeçalho `X-Webhook-Secret` está configurado?
4. ✅ Eventos estão marcados (Issue Created, Updated)?

**Teste manual:**
```bash
curl -X POST https://check-funcionando.preview.emergentagent.com/api/webhooks/jira \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: safe2go-webhook-secret-2025" \
  -d '{"webhookEvent":"jira:issue_created","issue":{"key":"TEST-1","fields":{"summary":"Teste"}}}'
```

---

## 📞 Precisa de Ajuda?

**Documentação Completa:** `/app/INTEGRACAO_JIRA.md`

**Endpoint do Webhook:**
```
POST https://check-funcionando.preview.emergentagent.com/api/webhooks/jira
```

**Última atualização:** Novembro 2025
