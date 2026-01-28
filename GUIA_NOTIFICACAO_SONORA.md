# 🔔 Guia: Como Ativar Notificações Sonoras

## 📋 **Por que o som não toca automaticamente?**

Navegadores modernos (Chrome, Firefox, Safari, Edge) **bloqueiam autoplay de áudio** por padrão para evitar sites que tocam sons indesejados. 

Para tocar som, é necessário que **o usuário interaja** com a página primeiro (clique em um botão, por exemplo).

---

## ✅ **Como Ativar o Som - Passo a Passo**

### **1️⃣ Abra a Página de Casos**
```
https://functional-check-1.preview.emergentagent.com/cases
```

### **2️⃣ Verifique a Conexão WebSocket**

Você verá um dos seguintes badges:

✅ **Conectado:**
```
Casos  🟢 Ao vivo  🔔 Ativar Som
```

❌ **Desconectado:**
```
Casos  ⚪ Desconectado
```

### **3️⃣ Clique no Botão "🔔 Ativar Som"**

Quando você clicar:
- Um som de teste curto tocará (bip rápido)
- O botão mudará para: **🔔 Som Ativo**
- Aparecerá um toast verde: "🔔 Notificações sonoras ativadas!"

### **4️⃣ Pronto! Agora os Sons Tocarão**

Quando um novo caso for criado no Jira, você ouvirá:
- 🔔 **Som "ding-dong"** (dois tons)
- 📱 **Toast verde** na tela
- 🔴 **Badge "NOVO"** no caso
- 📢 **Notificação do navegador** (se permitido)

---

## 🧪 **Teste Manual**

### **Opção 1: Criar Caso no Jira**
1. Acesse o Jira
2. Crie um novo caso qualquer
3. Aguarde 1-2 segundos
4. Você deve ouvir o som no Safe2Go

### **Opção 2: Usar Script de Teste**
```bash
# No servidor
bash /app/test_webhook_notification.sh
```

Este script:
- Simula um webhook do Jira
- Cria um caso teste
- Deve tocar o som se você ativou

---

## 🔍 **Solução de Problemas**

### **Problema 1: Não aparece "🟢 Ao vivo"**

**Causa:** WebSocket não conectou

**Solução:**
1. Recarregue a página (F5)
2. Verifique se backend está rodando:
```bash
sudo supervisorctl status backend
```
3. Veja logs do WebSocket:
```bash
tail -f /var/log/supervisor/backend.out.log | grep WebSocket
```

### **Problema 2: Aparece "Ao vivo" mas não tem botão "Ativar Som"**

**Causa:** O botão só aparece se som não está ativo

**Solução:**
- Se aparece **"🔔 Som Ativo"** → Som já está ativado! ✅
- Teste criando um caso no Jira

### **Problema 3: Cliquei em "Ativar Som" mas não toca quando caso é criado**

**Diagnóstico:**

#### **A. Verifique se WebSocket recebeu a mensagem:**
```bash
# Ver últimos logs
tail -n 50 /var/log/supervisor/backend.out.log | grep broadcast
```

Deve aparecer algo como:
```
📡 Broadcasting mensagem para 1 conexões: new_case
✅ Mensagem enviada com sucesso para 1 conexão
```

#### **B. Abra o Console do Navegador** (F12)

Deve aparecer:
```
✅ WebSocket conectado
🆕 Novo caso recebido via WebSocket: {caso...}
🔔 Som tocado com sucesso!
```

#### **C. Verifique Volume do Sistema**
- Som do computador não está mudo
- Volume do navegador não está zerado

### **Problema 4: Nenhum log de WebSocket no backend**

**Causa:** Nenhum cliente conectado

**Solução:**
1. Recarregue a página
2. Abra o console (F12) e veja se conectou
3. Se não conectar, verifique a URL do WebSocket:
```javascript
// No console do navegador
console.log(process.env.REACT_APP_BACKEND_URL)
```

---

## 🎯 **Fluxo Completo de Funcionamento**

```
1. Usuário abre página Safe2Go
   ↓
2. Frontend tenta conectar WebSocket
   ↓
3. Backend aceita conexão
   - Log: "WebSocket conectado. Total de conexões: 1"
   ↓
4. Frontend mostra: "🟢 Ao vivo  🔔 Ativar Som"
   ↓
5. Usuário clica "Ativar Som"
   - Som de teste toca
   - Mostra: "🔔 Som Ativo"
   ↓
6. Caso é criado no Jira
   - Webhook chega no backend
   - Backend salva no MongoDB
   ↓
7. Backend faz broadcast via WebSocket
   - Log: "📡 Broadcasting mensagem para N conexões"
   ↓
8. Frontend recebe mensagem
   - Console: "🆕 Novo caso recebido via WebSocket"
   ↓
9. Frontend toca som
   - Console: "🔔 Som tocado com sucesso!"
   ↓
10. Usuário ouve "ding-dong" 🎵
```

---

## 📊 **Status dos Indicadores**

| Indicador | Significado | O que fazer |
|-----------|-------------|-------------|
| 🟢 Ao vivo | WebSocket conectado | Tudo OK! Clique em "Ativar Som" |
| ⚪ Desconectado | WebSocket caiu | Aguarde reconexão automática |
| 🔔 Ativar Som | Som não habilitado | **CLIQUE AQUI** para ativar |
| 🔔 Som Ativo | Som funcionando | Pronto! Sons tocarão automaticamente |
| 🔴 NOVO | Caso recém-criado | Badge some em 30 segundos |

---

## 💡 **Dicas**

### **Mantenha a aba aberta**
- Se fechar a aba, o WebSocket desconecta
- Ao reabrir, precisa clicar em "Ativar Som" novamente

### **Múltiplas abas**
- Cada aba = 1 conexão WebSocket
- Todas receberão notificações
- Todas tocarão som (se ativado)

### **Notificação do navegador**
- Primeira vez: navegador pede permissão
- Clique em "Permitir"
- Notificações funcionam mesmo com aba minimizada

---

## 🎵 **Sobre o Som**

**Características:**
- Dois tons harmônicos (800Hz + 1000Hz)
- Duração: ~0.4 segundos
- Volume: 30% (não alto demais)
- Estilo: "ding-dong" amigável

**Por que dois tons?**
- Primeiro tom: Chama atenção
- Segundo tom: Confirma notificação
- Padrão comum em apps de mensagem

---

## ✅ **Checklist Rápido**

Para garantir que tudo funciona:

- [ ] Página carregada
- [ ] Badge "🟢 Ao vivo" aparece
- [ ] Clicou em "🔔 Ativar Som"
- [ ] Aparece "🔔 Som Ativo"
- [ ] Som de teste tocou
- [ ] Testou criando caso no Jira
- [ ] Som "ding-dong" tocou
- [ ] Badge "🔴 NOVO" apareceu
- [ ] Toast verde mostrou
- [ ] Notificação do navegador apareceu

---

**Última atualização:** 26 de Novembro de 2025
**Versão:** 3.1 - Sistema de Som com Ativação Manual
