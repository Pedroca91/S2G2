# 🔗 Integração Jira ↔️ Suporte Safe2Go

## 📋 Visão Geral

Esta integração permite que **todos os casos criados no Jira sejam automaticamente enviados** para o sistema Safe2Go em tempo real, sem necessidade de registro manual.

## ✨ Funcionalidades

- ✅ **Criação Automática**: Novos casos do Jira aparecem automaticamente no Safe2Go
- ✅ **Atualização em Tempo Real**: Mudanças no Jira são refletidas no sistema
- ✅ **Mapeamento de Status**: Status do Jira são convertidos para nossos status
- ✅ **Sem Duplicatas**: Sistema detecta e atualiza casos existentes
- ✅ **Seguro**: Webhook protegido com autenticação

## 🛠️ Como Configurar (Passo a Passo)

### Passo 1: Acesse as Configurações do Jira

1. Faça login no Jira como **Administrador**
2. Vá em **Configurações** (ícone de engrenagem no canto superior direito)
3. Clique em **Sistema**
4. No menu lateral, procure por **WebHooks**

### Passo 2: Criar Novo WebHook

1. Clique em **Criar um WebHook**
2. Preencha os campos:

**Nome do WebHook:**
```
Safe2Go - Sincronização de Casos
```

**Status:** 
```
Ativado ✅
```

**URL do WebHook:**
```
https://functional-check-1.preview.emergentagent.com/api/webhooks/jira
```

**Descrição:**
```
Envia automaticamente casos criados/atualizados para o sistema Safe2Go
```

### Passo 3: Configurar Eventos

Marque os seguintes eventos:

#### ✅ Eventos de Issue (Caso)
- [x] **Issue Created** (Caso Criado)
- [x] **Issue Updated** (Caso Atualizado)
- [x] **Issue Assigned** (Caso Atribuído)

#### ❌ Não marcar (opcional):
- [ ] Issue Deleted
- [ ] Issue Commented
- [ ] Issue Resolved

### Passo 4: Filtros (JQL) - Opcional

Se quiser enviar apenas casos específicos, use filtros JQL:

**Exemplo 1: Apenas projetos Safe2Go**
```jql
project = S2GSS
```

**Exemplo 2: Apenas casos urgentes**
```jql
priority in (Highest, High)
```

**Exemplo 3: Todos os casos (recomendado)**
```
Deixe em branco para enviar todos
```

### Passo 5: Autenticação - Cabeçalhos HTTP

Para segurança, adicione um cabeçalho personalizado:

**Nome do Cabeçalho:**
```
X-Webhook-Secret
```

**Valor:**
```
safe2go-webhook-secret-2025
```

### Passo 6: Testar o WebHook

1. Clique em **Salvar**
2. Clique em **Testar** no webhook criado
3. Selecione **Issue Created**
4. Clique em **Enviar**

**Resultado esperado:**
```json
{
  "status": "created",
  "case_id": "S2GSS-XXXXX"
}
```

## 📊 Mapeamento de Campos

### Jira → Safe2Go

| Campo no Jira | Campo no Safe2Go | Observação |
|---------------|------------------|------------|
| `key` | `jira_id` | Ex: S2GSS-10680 |
| `summary` | `title` | Título do caso |
| `description` | `description` | Descrição detalhada |
| `assignee.displayName` | `responsible` | Nome do responsável |
| `status.name` | `status` | Veja mapeamento abaixo |

### Mapeamento de Status

| Status no Jira | Status no Safe2Go |
|----------------|-------------------|
| To Do | Pendente |
| In Progress | Pendente |
| Done | Concluído |
| Closed | Concluído |
| Aguardando Cliente | Aguardando resposta do cliente |
| Waiting for Customer | Aguardando resposta do cliente |
| **Outros** | Pendente (padrão) |

## 🧪 Como Testar

### Teste 1: Criar Novo Caso

1. Crie um novo caso no Jira
2. Aguarde 2-3 segundos
3. Acesse o Safe2Go: https://functional-check-1.preview.emergentagent.com/
4. Vá em **Casos**
5. Verifique se o novo caso apareceu

### Teste 2: Atualizar Caso Existente

1. Edite um caso no Jira (mude o título ou status)
2. Aguarde 2-3 segundos
3. No Safe2Go, recarregue a página de Casos
4. Verifique se as alterações foram aplicadas

### Teste 3: Atribuir Responsável

1. No Jira, atribua um caso a um membro da equipe
2. No Safe2Go, verifique se o responsável foi atualizado

## 🔍 Logs e Monitoramento

### Ver Logs no Servidor

```bash
# Ver últimas 50 linhas do log do backend
tail -n 50 /var/log/supervisor/backend.out.log | grep webhook

# Ver apenas webhooks recebidos
tail -f /var/log/supervisor/backend.out.log | grep "webhook"
```

### Ver Histórico de WebHooks no Jira

1. Acesse **Configurações** → **Sistema** → **WebHooks**
2. Clique no webhook **Safe2Go**
3. Clique em **Ver histórico**
4. Veja todas as chamadas enviadas e suas respostas

## ⚙️ Configuração Avançada

### Adicionar Autenticação OAuth (Opcional)

Se o Jira exigir OAuth:

1. No backend, adicione validação de token
2. Configure OAuth 2.0 no Jira
3. Adicione `Authorization: Bearer <token>` nos headers

### Filtrar por Tipo de Issue

No JQL do webhook, adicione:

```jql
project = S2GSS AND issuetype = Bug
```

### Notificações por Email

Para receber email quando um caso for sincronizado, adicione ao endpoint:

```python
# Enviar email de notificação
send_email(
    to="suporte@safe2go.com",
    subject=f"Novo caso: {issue_key}",
    body=f"Caso {issue_key} foi criado/atualizado"
)
```

## 🚨 Solução de Problemas

### Problema 1: Webhook não está enviando

**Solução:**
1. Verifique se o webhook está **Ativado** no Jira
2. Teste manualmente usando o botão "Testar"
3. Verifique se a URL está correta
4. Confirme que o firewall permite conexões do Jira

### Problema 2: Casos não aparecem no Safe2Go

**Solução:**
1. Verifique os logs do backend:
   ```bash
   tail -f /var/log/supervisor/backend.out.log
   ```
2. Teste o endpoint manualmente:
   ```bash
   curl -X POST https://functional-check-1.preview.emergentagent.com/api/webhooks/jira \
     -H "Content-Type: application/json" \
     -H "X-Webhook-Secret: safe2go-webhook-secret-2025" \
     -d '{"webhookEvent":"jira:issue_created","issue":{"key":"TEST-1","fields":{"summary":"Teste"}}}'
   ```

### Problema 3: Casos duplicados

**Solução:**
- O sistema verifica automaticamente por `jira_id`
- Se houver duplicatas, verifique se há múltiplos webhooks configurados
- Desative webhooks duplicados no Jira

### Problema 4: Status não está sendo mapeado corretamente

**Solução:**
- Adicione o status personalizado no mapeamento do backend
- Edite `/app/backend/server.py` e adicione ao `status_map`

## 📝 Exemplo de Payload do Jira

Quando o Jira envia um webhook, o payload é assim:

```json
{
  "webhookEvent": "jira:issue_created",
  "issue": {
    "key": "S2GSS-10681",
    "fields": {
      "summary": "URGENTE - Sistema com erro",
      "description": "Descrição detalhada do problema",
      "status": {
        "name": "To Do"
      },
      "assignee": {
        "displayName": "João Silva"
      }
    }
  }
}
```

## 🔐 Segurança

### Recomendações:

1. ✅ Use HTTPS (já configurado)
2. ✅ Configure IP whitelist no Jira (permitir apenas IPs do Jira Cloud)
3. ✅ Use webhook secret (já configurado)
4. ✅ Monitore logs regularmente
5. ✅ Limite taxa de requisições se necessário

### IPs do Jira Cloud para Whitelist:

```
13.52.5.96/28
13.236.8.224/28
18.136.214.96/28
18.184.99.224/28
18.234.32.224/28
18.246.31.224/28
52.215.192.224/28
104.192.137.240/28
104.192.138.240/28
104.192.140.240/28
104.192.142.240/28
104.192.143.240/28
185.166.143.240/28
185.166.142.240/28
```

## 📞 Suporte

**Dúvidas sobre integração:**
- Documentação Jira: https://developer.atlassian.com/server/jira/platform/webhooks/
- Logs do sistema: `/var/log/supervisor/backend.out.log`

**Endpoint do WebHook:**
```
POST https://functional-check-1.preview.emergentagent.com/api/webhooks/jira
```

**Última atualização:** Novembro 2025
