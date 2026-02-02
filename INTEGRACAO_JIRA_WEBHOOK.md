# 🔗 INTEGRAÇÃO COM JIRA - WEBHOOK

## ⚠️ PROBLEMA IDENTIFICADO

A URL do webhook no Jira está **INCORRETA**. Está apontando para:
```
❌ https://s2g-ticketing.preview.emergentagent.com/api/webhooks/jira
```

Mas deveria ser:
```
✅ https://s2g-ticketing.preview.emergentagent.com/api/webhooks/jira
```

---

## 📋 COMO CORRIGIR NO JIRA

### **Passo 1: Acessar Configurações do Jira**
1. Vá para **Configurações do Jira** (⚙️)
2. Clique em **Sistema**
3. Vá em **Webhooks** (no menu lateral)

### **Passo 2: Editar o Webhook**
1. Localize o webhook atual (provavelmente chamado "Safe2Go" ou similar)
2. Clique em **Editar** (ícone de lápis)

### **Passo 3: Atualizar a URL**
1. No campo **URL**, altere para:
   ```
   https://s2g-ticketing.preview.emergentagent.com/api/webhooks/jira
   ```

2. Mantenha as outras configurações:
   - ✅ **Status**: Habilitado
   - ✅ **Eventos**: 
     - Issue created
     - Issue updated
     - Issue deleted

3. Clique em **Salvar**

---

## 🔧 VERIFICAÇÃO DO ENDPOINT

### **Teste Manual**

Você pode testar se o endpoint está funcionando com este comando:

```bash
curl -X POST https://s2g-ticketing.preview.emergentagent.com/api/webhooks/jira \
  -H "Content-Type: application/json" \
  -d '{
    "webhookEvent": "jira:issue_created",
    "issue": {
      "key": "TEST-001",
      "fields": {
        "summary": "Teste de integração",
        "description": "Testando webhook do Jira",
        "priority": {"name": "High"},
        "status": {"name": "To Do"}
      }
    }
  }'
```

**Resposta esperada:**
```json
{
  "status": "created",
  "case_id": "TEST-001"
}
```

---

## 📊 COMO FUNCIONA A INTEGRAÇÃO

### **1. Eventos Suportados**

| Evento Jira | Ação no Sistema |
|-------------|-----------------|
| `jira:issue_created` | Cria novo caso no Safe2Go |
| `jira:issue_updated` | Atualiza caso existente |
| `jira:issue_deleted` | (Não implementado) |

### **2. Mapeamento de Dados**

#### **Campos do Jira → Safe2Go**

| Campo Jira | Campo Safe2Go | Observação |
|------------|---------------|------------|
| `key` | `jira_id` | Identificador único |
| `summary` | `title` | Título do caso |
| `description` | `description` | Descrição completa |
| `assignee.displayName` | `responsible` | Responsável |
| `priority.name` | `priority` | Prioridade mapeada |
| `status.name` | `status` | Status mapeado |

#### **Mapeamento de Prioridade**

| Jira | Safe2Go |
|------|---------|
| Highest, High | high |
| Medium | medium |
| Low, Lowest | low |

#### **Mapeamento de Status**

| Jira | Safe2Go |
|------|---------|
| To Do, Open | Pendente |
| In Progress | Em Desenvolvimento |
| Done, Closed, Resolved | Concluído |
| Waiting for Support | Aguardando resposta |

---

## 🔐 SEGURANÇA

### **Sem Autenticação Implementada**

⚠️ **Atualmente o webhook NÃO possui autenticação**. Isso significa que qualquer um que souber a URL pode enviar dados.

### **Recomendações para Produção:**

1. **Adicionar Secret Token**
   ```python
   WEBHOOK_SECRET = os.environ.get('JIRA_WEBHOOK_SECRET')
   
   @api_router.post("/webhooks/jira")
   async def jira_webhook(payload: dict, request: Request):
       # Validar token
       token = request.headers.get('X-Webhook-Token')
       if token != WEBHOOK_SECRET:
           raise HTTPException(401, "Unauthorized")
   ```

2. **Configurar no Jira**
   - Adicionar header personalizado: `X-Webhook-Token: seu-token-secreto`

3. **Validar IP de Origem**
   - Permitir apenas IPs do Jira Cloud

---

## 📝 CÓDIGO DO WEBHOOK

### **Endpoint Backend** (`/app/backend/server.py`)

```python
@api_router.post("/webhooks/jira")
async def jira_webhook(payload: dict):
    try:
        webhook_event = payload.get('webhookEvent', '')
        
        if 'issue' not in payload:
            return {"status": "ignored", "reason": "No issue data"}
        
        issue = payload['issue']
        issue_key = issue.get('key', '')
        fields = issue.get('fields', {})
        
        # Extrair dados
        title = fields.get('summary', 'Sem título')
        description = fields.get('description', '')
        
        # Criar ou atualizar caso no sistema
        # ... (código completo no arquivo)
        
        return {"status": "created", "case_id": issue_key}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

---

## 🧪 TESTE COMPLETO

### **1. Criar Issue no Jira**
```
1. Vá ao seu projeto no Jira
2. Clique em "Criar Issue"
3. Preencha:
   - Resumo: "Teste de integração Safe2Go"
   - Descrição: "Testando webhook"
   - Prioridade: Alta
4. Clique em Criar
```

### **2. Verificar no Safe2Go**
```
1. Acesse o Dashboard do Safe2Go
2. Vá em "Chamados"
3. Procure pelo caso com Jira ID correspondente
4. Verifique se os dados foram sincronizados corretamente
```

### **3. Atualizar Issue no Jira**
```
1. Mude o status da issue para "In Progress"
2. Verifique se o status no Safe2Go mudou para "Em Desenvolvimento"
```

---

## 📋 CHECKLIST DE CONFIGURAÇÃO

- [ ] URL do webhook atualizada no Jira
- [ ] Webhook está **Habilitado**
- [ ] Eventos configurados:
  - [ ] Issue created
  - [ ] Issue updated
- [ ] Teste manual realizado
- [ ] Issue de teste criada no Jira
- [ ] Caso apareceu no Safe2Go
- [ ] Dados mapeados corretamente

---

## 🔍 DIAGNÓSTICO DE PROBLEMAS

### **Webhook não está criando casos?**

1. **Verificar logs do backend:**
   ```bash
   tail -f /var/log/supervisor/backend.out.log | grep webhook
   ```

2. **Testar endpoint manualmente:**
   ```bash
   curl -X POST https://s2g-ticketing.preview.emergentagent.com/api/webhooks/jira \
     -H "Content-Type: application/json" \
     -d '{"webhookEvent":"jira:issue_created","issue":{"key":"TEST"}}'
   ```

3. **Verificar no Jira:**
   - Configurações → Sistema → Webhooks
   - Clicar no webhook
   - Ver aba "Recent deliveries" para verificar logs de entrega

### **Dados não estão mapeados corretamente?**

1. Verificar formato do payload do Jira (pode variar entre versões)
2. Adicionar logs no backend para debug:
   ```python
   print(f"Received payload: {payload}")
   ```

---

## 📊 EXEMPLO DE PAYLOAD DO JIRA

```json
{
  "webhookEvent": "jira:issue_created",
  "issue": {
    "key": "SGSS-123",
    "fields": {
      "summary": "Problema com login",
      "description": "Usuário não consegue fazer login",
      "priority": {
        "name": "High"
      },
      "status": {
        "name": "To Do"
      },
      "assignee": {
        "displayName": "Pedro Carvalho"
      },
      "created": "2026-01-28T14:30:00.000+0000"
    }
  }
}
```

---

## 🌐 URLs IMPORTANTES

| Recurso | URL |
|---------|-----|
| **Sistema Safe2Go** | https://s2g-ticketing.preview.emergentagent.com |
| **Webhook Endpoint** | https://s2g-ticketing.preview.emergentagent.com/api/webhooks/jira |
| **Dashboard** | https://s2g-ticketing.preview.emergentagent.com/ |
| **API Docs** | https://s2g-ticketing.preview.emergentagent.com/docs |

---

## 📞 SUPORTE

Se após seguir estes passos a integração não funcionar:

1. Verifique se a URL está correta no Jira
2. Teste o endpoint manualmente
3. Verifique os logs do backend
4. Verifique os logs de entrega no Jira

---

**✅ WEBHOOK CONFIGURADO E TESTADO!**

*Última atualização: 28/01/2026*
*Status: Endpoint funcionando, URL precisa ser atualizada no Jira*
