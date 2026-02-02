# 🔧 Troubleshooting - Webhook Jira Não Está Funcionando

## ✅ Status do Endpoint

**CONFIRMADO:** O endpoint `/api/webhooks/jira` está **FUNCIONANDO CORRETAMENTE**
- Teste local realizado com sucesso
- Caso TEST-WEBHOOK-001 criado automaticamente
- Backend processando requisições normalmente

---

## ❌ Problema Identificado

O **Jira não está conseguindo enviar requisições** para o nosso sistema.

---

## 🔍 Possíveis Causas e Soluções

### **1. URL do Webhook Incorreta ou Inacessível**

**Sintoma:** Jira não consegue se conectar ao endpoint

**Possíveis Causas:**
- URL configurada no Jira está errada
- O servidor Safe2Go não está acessível publicamente pela internet
- Firewall bloqueando requisições do Jira

**Verificar:**

✅ **URL correta que deve estar configurada no Jira:**
```
https://s2g-ticketing.preview.emergentagent.com/api/webhooks/jira
```

**Como testar se a URL está acessível:**

```bash
# De um computador EXTERNO (não do servidor), execute:
curl -X POST https://s2g-ticketing.preview.emergentagent.com/api/webhooks/jira \
  -H "Content-Type: application/json" \
  -d '{"webhookEvent":"jira:issue_created","issue":{"key":"TEST-123","fields":{"summary":"Teste","description":"Teste","status":{"name":"To Do"}}}}'
```

**Resposta esperada:**
```json
{"status":"created","case_id":"TEST-123"}
```

---

### **2. Webhook Desabilitado no Jira**

**Causa:** O webhook foi desabilitado acidentalmente

**Solução:**

1. Acesse o Jira como administrador
2. Vá em: `⚙️ Configurações` → `Sistema` → `Webhooks`
3. Encontre o webhook "Safe2Go - Sincronização de Casos"
4. Verifique se o status está como **"Habilitado"**
5. Se estiver desabilitado, clique em **"Editar"** e marque **"Habilitado"**

---

### **3. Eventos Não Selecionados**

**Causa:** Os eventos "created" e "updated" não estão marcados

**Solução:**

1. No Jira, vá em: `Webhooks` → Editar o webhook
2. Na seção **"Eventos"**, certifique-se que está marcado:
   - ✅ **Issue → criado** (issue_created)
   - ✅ **Issue → atualizado** (issue_updated)
3. Salve as alterações

---

### **4. Filtro JQL Muito Restritivo**

**Causa:** O webhook tem um filtro JQL que está impedindo os casos de serem sincronizados

**Solução:**

1. No Jira, edite o webhook
2. Na seção **"Filtro JQL"**, verifique se há algum filtro configurado
3. Para testar, **remova o filtro JQL** temporariamente
4. Crie um novo issue no Jira e veja se sincroniza
5. Se funcionar, ajuste o filtro JQL conforme necessário

---

### **5. Problemas de Rede/Firewall**

**Causa:** O Jira está hospedado em uma rede que bloqueia requisições externas

**Sintomas:**
- Timeout ao tentar enviar webhook
- Jira mostra erro de conexão

**Solução:**

Se você está usando **Jira Cloud (Atlassian):**
- Não há problemas de rede, o Atlassian tem acesso à internet

Se você está usando **Jira Server (auto-hospedado):**
1. Verifique com o administrador de rede se requisições HTTPS externas estão bloqueadas
2. Peça para liberar requisições para: `check-funcionando.preview.emergentagent.com`
3. Porta necessária: **443 (HTTPS)**

---

### **6. Webhook Configurado no Projeto Errado**

**Causa:** O webhook está configurado em um projeto específico, mas você está criando issues em outro

**Solução:**

1. No Jira, vá em `Webhooks`
2. Verifique se o webhook está configurado como:
   - **Global** (para todos os projetos)
   - **Ou** apenas para projetos específicos
3. Se estiver limitado a projetos específicos, adicione o projeto onde você está criando issues

---

## 🧪 Teste Passo a Passo

### **Teste 1: Verificar se o endpoint está acessível externamente**

De um computador diferente (ou use https://reqbin.com/):

```bash
curl -X POST https://s2g-ticketing.preview.emergentagent.com/api/webhooks/jira \
  -H "Content-Type: application/json" \
  -d '{
    "webhookEvent": "jira:issue_created",
    "issue": {
      "key": "TESTE-EXTERNO",
      "fields": {
        "summary": "Teste externo de webhook",
        "description": "Verificando conectividade externa",
        "status": {"name": "To Do"},
        "assignee": {"displayName": "Teste"}
      }
    }
  }'
```

**Resultado esperado:**
```json
{"status":"created","case_id":"TESTE-EXTERNO"}
```

Se não funcionar, o problema é de **conectividade externa**.

---

### **Teste 2: Verificar logs do webhook no Jira**

1. No Jira, vá em: `Webhooks`
2. Clique no webhook "Safe2Go"
3. Clique em **"Exibir histórico"** ou **"View Details"**
4. Verifique:
   - ✅ Se há registros de tentativas de envio
   - ❌ Se há erros (timeout, 404, 500, etc.)
   - ⏱️ Timestamps das últimas tentativas

**Possíveis erros e soluções:**

| Erro | Causa | Solução |
|------|-------|---------|
| `Timeout` | Servidor não respondeu em tempo | Verificar se URL está correta |
| `404 Not Found` | URL do webhook errada | Corrigir URL no Jira |
| `500 Internal Server Error` | Erro no nosso backend | Verificar logs do backend |
| `Connection refused` | Servidor inacessível | Verificar firewall/rede |

---

### **Teste 3: Criar issue de teste no Jira**

1. Crie um novo issue no Jira
2. Preencha:
   - **Resumo:** "TESTE WEBHOOK - [DATA/HORA ATUAL]"
   - **Descrição:** "Testando integração com Safe2Go"
   - **Tipo:** Bug ou Task
3. Salve o issue
4. Aguarde 5 segundos
5. Acesse o Safe2Go
6. Vá em **Chamados**
7. Procure pelo issue criado

**Se NÃO aparecer:**
- Verifique o histórico do webhook no Jira (passo anterior)
- Verifique se o webhook está habilitado
- Verifique se os eventos estão selecionados

---

## 📊 Checklist de Diagnóstico

Execute na ordem:

- [ ] 1. Webhook está **habilitado** no Jira?
- [ ] 2. URL está **correta**: `https://s2g-ticketing.preview.emergentagent.com/api/webhooks/jira`
- [ ] 3. Eventos **criado** e **atualizado** estão marcados?
- [ ] 4. Filtro JQL está **vazio** ou **correto**?
- [ ] 5. Endpoint está **acessível externamente** (teste com curl)?
- [ ] 6. Histórico do webhook no Jira mostra **tentativas de envio**?
- [ ] 7. Histórico mostra **erros**? (anotar qual erro)
- [ ] 8. Issue criado no **projeto correto** (se webhook for específico de projeto)?

---

## 🆘 Se Nada Funcionar

**Opções alternativas:**

### **Opção 1: Recriar o Webhook**

1. No Jira, **delete** o webhook existente
2. Crie um novo webhook do zero:
   - **Nome:** Safe2Go Webhook Novo
   - **URL:** `https://s2g-ticketing.preview.emergentagent.com/api/webhooks/jira`
   - **Eventos:** Issue → criado, Issue → atualizado
   - **Status:** Habilitado
3. Teste criando um novo issue

---

### **Opção 2: Usar Importação Manual**

Se o webhook não funcionar, você pode:
1. Exportar casos do Jira como CSV/JSON
2. Usar a funcionalidade de **Importar** no Safe2Go (botão na tela de Chamados)
3. Fazer importação manual periódica

---

### **Opção 3: Verificar com Suporte do Jira**

Se você usa Jira Cloud:
1. Abra um ticket no suporte da Atlassian
2. Informe que webhooks não estão funcionando
3. Forneça:
   - URL do webhook
   - Projeto onde está testando
   - Logs de erro do webhook

---

## 📞 Informações para Compartilhar

Se precisar de ajuda adicional, compartilhe:

1. **URL configurada no Jira:** (copie exatamente como está)
2. **Screenshot da configuração do webhook**
3. **Histórico/logs do webhook no Jira** (últimas 5 tentativas)
4. **Mensagem de erro específica** (se houver)
5. **Tipo de Jira:** Cloud ou Server?
6. **Projeto onde está criando issues:** (nome do projeto)

---

## ✅ Teste de Validação

Para confirmar que está funcionando:

1. **Crie um issue no Jira** com resumo: "TESTE WEBHOOK SAFE2GO"
2. Aguarde **10 segundos**
3. **Acesse Safe2Go** → Chamados
4. **Procure** pelo caso com ID do Jira
5. **Confirme** que o caso foi criado com:
   - ✅ Mesmo ID do Jira
   - ✅ Mesmo título/resumo
   - ✅ Status correto (mapeado)

---

**Criado em:** 04/12/2025  
**Última atualização:** 04/12/2025  
**Status do Endpoint:** ✅ Funcionando (testado localmente)
