# 🔗 Configuração do Webhook Jira - Safe2Go Helpdesk

## ✅ Status: **FUNCIONANDO**

O webhook do Jira está **totalmente funcional** e pronto para uso!

---

## 📋 Informações da Configuração

### 🌐 **URL do Webhook**
```
https://check-funcionando.preview.emergentagent.com/api/webhooks/jira
```

### 📡 **Eventos que devem ser habilitados:**
- ✅ **Issue → created** (quando um chamado é criado)
- ✅ **Issue → updated** (quando um chamado é atualizado)

### 🔒 **Autenticação:**
- Não requer autenticação (endpoint público)
- O webhook está protegido contra spam por validação de payload

---

## 🎯 Como Funciona

### 1️⃣ **Quando um chamado é criado no Jira:**
- O webhook recebe os dados
- Extrai informações: título, descrição, responsável, status
- Detecta automaticamente a **seguradora** (AVLA, ESSOR, Daycoval) baseado no texto
- Categoriza automaticamente (Reprocessamento, Erro Corretor, etc.)
- Cria o chamado no sistema Safe2Go

### 2️⃣ **Quando um chamado é atualizado no Jira:**
- O webhook atualiza o chamado existente no Safe2Go
- Sincroniza: título, descrição, responsável, status, categoria

### 3️⃣ **Mapeamento de Status:**
| Status Jira | Status Safe2Go |
|------------|---------------|
| To Do | Pendente |
| In Progress | Pendente |
| Done | Concluído |
| Closed | Concluído |
| Aguardando Cliente | Aguardando resposta |
| Waiting for Customer | Aguardando resposta |

---

## 🛠️ Passo a Passo para Configurar no Jira

### **1. Acesse Configurações de Sistema**
- No Jira, vá em: `⚙️ Configurações` → `Sistema`

### **2. Abra Webhooks**
- No menu lateral, clique em: `Webhooks`

### **3. Criar Novo Webhook**
- Clique em **"Criar webhook"** ou **"+ Criar um webhook"**

### **4. Preencha os Campos:**

**Nome:**
```
Safe2Go - Sincronização de Casos
```

**Status:**
- ✅ Habilitado

**URL:**
```
https://check-funcionando.preview.emergentagent.com/api/webhooks/jira
```

**Descrição (opcional):**
```
Webhook para sincronizar automaticamente chamados do Jira com o sistema Safe2Go Helpdesk. 
Criado em: 02/12/2025
Última atualização: 02/12/2025
Responsável: Suporte Safe2Go
```

**Eventos:**
Marque as seguintes opções:

- ✅ **criado** (Issue → created)
- ✅ **atualizado** (Issue → updated)
- ✅ **excluído** (Issue → deleted) - opcional

**Filtro JQL (opcional):**
Se quiser sincronizar apenas issues específicas, use:
```
project = "SEU_PROJETO" AND type = "Bug"
```

### **5. Salvar**
- Clique em **"Criar"** ou **"Salvar"**

---

## 🧪 Como Testar

### **Teste 1: Criar um novo chamado no Jira**
1. Crie um novo issue no Jira
2. Preencha: Título, Descrição, Responsável
3. Mencione a seguradora no título ou descrição (ex: "Problema AVLA")
4. Salve o issue
5. Verifique no Safe2Go se o chamado apareceu automaticamente

### **Teste 2: Via curl (teste manual)**
```bash
curl -X POST https://check-funcionando.preview.emergentagent.com/api/webhooks/jira \
  -H "Content-Type: application/json" \
  -d '{
    "webhookEvent": "jira:issue_created",
    "issue": {
      "key": "PROJ-123",
      "fields": {
        "summary": "Problema com sistema AVLA",
        "description": "Descrição do problema",
        "status": {"name": "To Do"},
        "assignee": {"displayName": "Nome do Responsável"}
      }
    }
  }'
```

**Resposta esperada:**
```json
{
  "status": "created",
  "case_id": "PROJ-123"
}
```

---

## 🔍 Detecção Automática

### **Seguradoras Detectadas:**
O sistema detecta automaticamente a seguradora quando o texto contém:
- `AVLA` → Seguradora: AVLA
- `ESSOR` → Seguradora: ESSOR
- `DAYCOVAL` ou `Daycoval` → Seguradora: Daycoval

### **Categorias Detectadas:**
- `reprocessamento` → Categoria: Reprocessamento
- `erro corretor` ou `corretor` → Categoria: Erro Corretor
- `nova lei` ou `adequação` → Categoria: Adequação Nova Lei
- `boleto` → Categoria: Erro Boleto
- `endosso` → Categoria: Problema Endosso
- `sumiço` ou `sumico` → Categoria: Sumiço de Dados
- `integra` → Categoria: Integração
- Outros casos → Categoria: Outros

---

## 📊 Logs e Monitoramento

### **Verificar se webhook está funcionando:**
1. Acesse o Safe2Go
2. Vá em **Chamados**
3. Verifique se os chamados do Jira aparecem com o ID correto (ex: `PROJ-123`)

### **Logs do Backend:**
Para ver os logs do webhook no servidor:
```bash
tail -f /var/log/supervisor/backend.out.log | grep -i "webhook\|jira"
```

---

## ❓ Troubleshooting

### **Problema: Webhook não está criando chamados**

**Possíveis causas:**
1. URL incorreta
2. Eventos não selecionados (created/updated)
3. Webhook desabilitado no Jira

**Solução:**
- Verifique a URL: `https://check-funcionando.preview.emergentagent.com/api/webhooks/jira`
- Confirme que os eventos estão marcados
- Teste via curl para confirmar que o endpoint está acessível

### **Problema: Chamados sendo duplicados**

**Causa:**
Webhook configurado múltiplas vezes

**Solução:**
- Vá em Webhooks no Jira
- Verifique se há múltiplos webhooks com a mesma URL
- Desabilite os webhooks duplicados

### **Problema: Seguradora não está sendo detectada**

**Causa:**
Nome da seguradora não está no título ou descrição

**Solução:**
- Inclua o nome da seguradora (AVLA, ESSOR, Daycoval) no título ou descrição do issue
- Ou edite o chamado manualmente no Safe2Go após a criação

---

## 🎉 Confirmação

✅ **Webhook testado e funcionando**
- Endpoint: `/api/webhooks/jira` ativo
- Teste realizado: Caso TEST-123 criado com sucesso
- Detecção automática: Seguradora AVLA identificada
- Status: Pendente mapeado corretamente

---

## 📞 Suporte

Se precisar de ajuda adicional com a configuração:
1. Verifique se a URL está correta
2. Teste com curl para confirmar conectividade
3. Verifique os logs do sistema

**Arquivo criado em:** 02/12/2025  
**Última atualização:** 02/12/2025
