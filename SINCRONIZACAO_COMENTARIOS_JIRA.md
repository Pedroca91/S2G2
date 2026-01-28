# 💬 SINCRONIZAÇÃO DE COMENTÁRIOS JIRA ↔ SAFE2GO

## ✅ IMPLEMENTAÇÃO CONCLUÍDA

A sincronização **bidirecional** de comentários entre Jira e Safe2Go foi implementada!

---

## 🔄 FLUXOS DE SINCRONIZAÇÃO

### **1. Jira → Safe2Go** ✅
Quando alguém comenta no Jira:
- ✅ Webhook recebe o evento `comment_created`
- ✅ Comentário é salvo no Safe2Go
- ✅ Notificação é criada para o responsável
- ✅ Aparece na tela de detalhes do caso

### **2. Safe2Go → Jira** ✅
Quando alguém comenta no Safe2Go:
- ✅ Comentário é enviado automaticamente para o Jira via API
- ✅ Aparece na issue do Jira com prefixo `[Safe2Go - Nome do Autor]`
- ✅ Comentários internos **NÃO** são sincronizados (apenas visíveis no Safe2Go)

---

## ⚙️ CONFIGURAÇÃO NECESSÁRIA

### **Passo 1: Obter Credenciais do Jira**

#### **1.1. Criar API Token**
1. Acesse: https://id.atlassian.com/manage-profile/security/api-tokens
2. Clique em **"Create API token"**
3. Dê um nome: `Safe2Go Integration`
4. Copie o token (guarde bem, não será mostrado novamente!)

#### **1.2. Obter URL do Jira**
Sua URL base do Jira, exemplo:
- ✅ `https://sua-empresa.atlassian.net`
- ❌ Não inclua `/rest/api` ou paths

#### **1.3. Email de Login**
O email que você usa para fazer login no Jira

---

### **Passo 2: Configurar no Safe2Go**

Adicione as credenciais no arquivo `.env` do backend:

```bash
# No servidor, edite o arquivo /app/backend/.env
JIRA_URL=https://sua-empresa.atlassian.net
JIRA_EMAIL=seu-email@empresa.com
JIRA_API_TOKEN=seu-token-aqui
```

**Exemplo:**
```bash
JIRA_URL=https://acme.atlassian.net
JIRA_EMAIL=admin@acme.com
JIRA_API_TOKEN=ATATT3xFfGF0abcdefg1234567890hijklmnopqrstuvwxyz
```

---

### **Passo 3: Configurar Webhook no Jira para Comentários**

#### **3.1. Acessar Webhooks**
1. Jira → **Configurações** ⚙️
2. **Sistema** → **Webhooks**
3. Clique no webhook existente "Safe2Go"

#### **3.2. Adicionar Eventos de Comentários**
Marque os eventos:
- ✅ **Issue created**
- ✅ **Issue updated**
- ✅ **Comment created** ← **NOVO!**
- ✅ **Comment updated** ← **NOVO!**

#### **3.3. Salvar**
Clique em **Update** ou **Salvar**

---

### **Passo 4: Reiniciar Backend**

Para aplicar as novas credenciais:

```bash
sudo supervisorctl restart backend
```

---

## 🧪 TESTAR A SINCRONIZAÇÃO

### **Teste 1: Jira → Safe2Go**

1. **Abra uma issue no Jira**
2. **Adicione um comentário:** "Teste de sincronização do Jira"
3. **Vá no Safe2Go:**
   - Abra o caso correspondente
   - Vá na aba "Comentários"
   - Você verá o comentário com autor do Jira

### **Teste 2: Safe2Go → Jira**

1. **Abra um caso no Safe2Go** (que tenha Jira ID)
2. **Adicione um comentário:** "Teste de sincronização do Safe2Go"
3. **Marque como público** (não interno)
4. **Envie**
5. **Vá no Jira:**
   - Abra a issue correspondente
   - Você verá: `[Safe2Go - Seu Nome] Teste de sincronização do Safe2Go`

---

## 📊 COMPORTAMENTO DOS COMENTÁRIOS

### **Comentários Públicos** 👁️
```
Safe2Go: Público (✓)
         ↓
Jira:    Visível para todos
```

### **Comentários Internos** 🔒
```
Safe2Go: Interno (✓)
         ↓
Jira:    NÃO sincronizado (fica apenas no Safe2Go)
```

### **Comentários do Jira** 📥
```
Jira:    Qualquer comentário
         ↓
Safe2Go: Sempre público (não tem opção de interno no Jira)
```

---

## 🔐 SEGURANÇA

### **API Token**
- ✅ Token armazenado apenas no backend (`.env`)
- ✅ Nunca exposto ao frontend
- ✅ Criptografado durante transmissão (HTTPS)

### **Comentários Internos**
- ✅ Visíveis apenas para admins no Safe2Go
- ✅ Nunca enviados ao Jira
- ✅ Úteis para discussões internas da equipe

---

## 📋 FORMATO DOS COMENTÁRIOS

### **No Safe2Go (vindos do Jira)**
```
Autor: João Silva (Jira)
Data: 28/01/2026 14:30
Comentário: Este é um comentário do Jira
```

### **No Jira (vindos do Safe2Go)**
```
[Safe2Go - Maria Santos] Este é um comentário do Safe2Go
```

O prefixo `[Safe2Go - Nome]` identifica que o comentário veio do Safe2Go.

---

## 🔧 CÓDIGO IMPLEMENTADO

### **Backend - Receber Comentários do Jira**
```python
@api_router.post("/webhooks/jira")
async def jira_webhook(payload: dict):
    # Detectar evento de comentário
    if 'comment' in webhook_event:
        return await handle_jira_comment(payload)
```

### **Backend - Enviar Comentários ao Jira**
```python
async def send_comment_to_jira(jira_id: str, comment_text: str, author_name: str):
    # Criar autenticação
    auth = base64.b64encode(f"{email}:{token}".encode()).decode()
    
    # Enviar via API REST do Jira
    await httpx.post(
        f"{jira_url}/rest/api/3/issue/{jira_id}/comment",
        json={"body": {...}},
        headers={"Authorization": f"Basic {auth}"}
    )
```

### **Backend - Criar Comentário**
```python
@api_router.post("/cases/{case_id}/comments")
async def create_comment(...):
    # Salvar no banco
    await db.comments.insert_one(comment)
    
    # Sincronizar com Jira (se não for interno)
    if not is_internal and case.get('jira_id'):
        await send_comment_to_jira(...)
```

---

## 🚨 SOLUÇÃO DE PROBLEMAS

### **Comentários do Safe2Go não aparecem no Jira**

1. **Verificar credenciais:**
   ```bash
   cat /app/backend/.env | grep JIRA
   ```
   - Todas as 3 variáveis devem estar preenchidas

2. **Verificar logs do backend:**
   ```bash
   tail -f /var/log/supervisor/backend.out.log | grep -i jira
   ```
   - Procure por mensagens de erro

3. **Testar credenciais manualmente:**
   ```bash
   # Substituir valores
   curl -u "seu-email@empresa.com:seu-token" \
     https://sua-empresa.atlassian.net/rest/api/3/myself
   ```
   - Deve retornar seus dados do Jira

### **Comentários do Jira não aparecem no Safe2Go**

1. **Verificar webhook:**
   - Jira → Sistema → Webhooks
   - Eventos de comentários devem estar marcados
   - Ver "Recent deliveries" para logs

2. **Verificar se o caso existe:**
   - O caso com aquele Jira ID deve existir no Safe2Go
   - Caso não exista, comentário será ignorado

---

## 📊 DADOS SALVOS

### **Comentário no MongoDB**
```json
{
  "id": "uuid",
  "case_id": "caso-id",
  "jira_comment_id": "10001",
  "author": "João Silva",
  "text": "Comentário do Jira",
  "is_internal": false,
  "created_at": "2026-01-28T14:30:00Z",
  "synced_from_jira": true
}
```

---

## ✅ CHECKLIST DE CONFIGURAÇÃO

- [ ] API Token criado no Jira
- [ ] URL do Jira obtida
- [ ] Email de login identificado
- [ ] Credenciais adicionadas ao `.env`
- [ ] Backend reiniciado
- [ ] Webhook configurado para eventos de comentários
- [ ] Teste Jira → Safe2Go realizado
- [ ] Teste Safe2Go → Jira realizado

---

## 📞 COMANDOS ÚTEIS

```bash
# Ver logs de sincronização
tail -f /var/log/supervisor/backend.out.log | grep -E "comment|jira"

# Reiniciar backend
sudo supervisorctl restart backend

# Ver comentários no banco
mongo safe2go_helpdesk --eval "db.comments.find().pretty()"
```

---

## 🌐 RECURSOS

| Recurso | URL |
|---------|-----|
| **Criar API Token** | https://id.atlassian.com/manage-profile/security/api-tokens |
| **Jira REST API Docs** | https://developer.atlassian.com/cloud/jira/platform/rest/v3/ |
| **Webhooks Jira** | https://developer.atlassian.com/cloud/jira/platform/webhooks/ |

---

**✅ SINCRONIZAÇÃO BIDIRECIONAL DE COMENTÁRIOS IMPLEMENTADA!**

*Última atualização: 28/01/2026*
*Versão: 1.0*
*Status: Aguardando configuração de credenciais*
