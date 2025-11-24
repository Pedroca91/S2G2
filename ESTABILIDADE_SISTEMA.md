# 🛡️ Estabilidade do Sistema - Suporte Safe2Go

## 🔍 Diagnóstico do Problema

### Por que o sistema estava "caindo"?

**Problema Identificado:**
O sistema **não estava caindo**, mas sim **reiniciando automaticamente** devido ao **modo de desenvolvimento** (hot-reload).

### O que estava acontecendo:

```
Backend rodando com --reload
      ↓
Detecta mudança em qualquer arquivo
      ↓
Reinicia automaticamente
      ↓
Você perde a conexão temporariamente
      ↓
Parece que o sistema "caiu"
```

## 📊 Evidências

### Logs do Backend:
```
WARNING: WatchFiles detected changes in 'server.py'. Reloading...
INFO: Shutting down
INFO: Application shutdown complete.
INFO: Started server process [245]
```

**Isso significa:** O backend estava funcionando corretamente, mas reiniciando muito.

## ✅ Soluções Implementadas

### 1. Diagnóstico Completo
- ✅ Verificado status dos serviços (todos RUNNING)
- ✅ Verificado uso de memória (45GB disponíveis de 62GB)
- ✅ Verificado uso de CPU (normal)
- ✅ Identificado hot-reload como causa

### 2. Configuração Atual

**Backend:**
```bash
# Modo Desenvolvimento (ATUAL - com auto-reload)
command=uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload

# ⚠️ Problema: --reload faz reiniciar a cada mudança
```

**Frontend:**
```bash
# React Development Server (ATUAL)
command=yarn start

# ⚠️ Problema: Hot-reload do React também reinicia frequentemente
```

### 3. Configuração Recomendada para Produção

Criada em: `/app/supervisord_production.conf`

**Mudanças:**
- ❌ Removido `--reload` do backend
- ✅ Adicionado 2 workers para melhor performance
- ✅ Configurado log rotation (50MB max)
- ✅ Aumentado startretries (3 tentativas)
- ✅ MongoDB com prioridade alta

## 🎯 Quando Aplicar a Configuração de Produção?

### Manter modo desenvolvimento (atual) se:
- ✅ Você ainda está fazendo alterações frequentes no código
- ✅ Precisa ver mudanças imediatamente
- ✅ Está em fase de desenvolvimento/teste

### Mudar para modo produção se:
- ✅ Sistema está pronto e estável
- ✅ Não vai fazer mais alterações frequentes
- ✅ Quer máxima estabilidade
- ✅ Vai colocar em produção real

## 🔧 Como Aplicar a Configuração de Produção

**Passo 1: Fazer backup da configuração atual**
```bash
sudo cp /etc/supervisor/conf.d/supervisord.conf /etc/supervisor/conf.d/supervisord.conf.backup
```

**Passo 2: Aplicar nova configuração**
```bash
sudo cp /app/supervisord_production.conf /etc/supervisor/conf.d/supervisord.conf
```

**Passo 3: Recarregar supervisor**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all
```

**Passo 4: Verificar status**
```bash
sudo supervisorctl status
```

## 📈 Monitoramento da Estabilidade

### Verificar se os serviços estão rodando:
```bash
sudo supervisorctl status
```

**Resultado esperado:**
```
backend     RUNNING   pid 29, uptime 2:30:15
frontend    RUNNING   pid 31, uptime 2:30:15
mongodb     RUNNING   pid 32, uptime 2:30:15
```

### Verificar logs em tempo real:
```bash
# Backend
tail -f /var/log/supervisor/backend.out.log

# Frontend
tail -f /var/log/supervisor/frontend.out.log

# Erros do backend
tail -f /var/log/supervisor/backend.err.log
```

### Verificar uso de recursos:
```bash
# Memória
free -h

# CPU e processos
top -b -n 1 | head -20

# Uso de disco
df -h
```

## 🚨 Sinais de Problemas Reais

### ❌ Sistema realmente caindo:
- Serviços aparecem como **STOPPED** ou **FATAL**
- Mensagens de erro **ERROR** ou **FATAL** nos logs
- Memória acima de 90% de uso
- CPU constantemente acima de 90%

### ✅ Sistema funcionando (reiniciando normalmente):
- Serviços aparecem como **RUNNING**
- Logs mostram **Reloading** ou **Restarting**
- Memória e CPU em níveis normais
- Uptime baixo mas constante reinício

## 🔍 Comandos Úteis de Diagnóstico

### Ver status completo:
```bash
sudo supervisorctl status
ps aux | grep -E "uvicorn|node|mongod"
```

### Ver últimos erros:
```bash
tail -n 50 /var/log/supervisor/backend.err.log
tail -n 50 /var/log/supervisor/frontend.err.log
```

### Reiniciar serviços manualmente:
```bash
# Reiniciar backend
sudo supervisorctl restart backend

# Reiniciar frontend
sudo supervisorctl restart frontend

# Reiniciar tudo
sudo supervisorctl restart all
```

### Ver tempo de execução:
```bash
sudo supervisorctl status | grep uptime
```

## 💡 Dicas de Estabilidade

### 1. Evite editar arquivos diretamente em produção
- Faça alterações em ambiente de desenvolvimento
- Teste antes de aplicar
- Use git para controle de versão

### 2. Monitore regularmente
- Verifique status dos serviços 1x por dia
- Olhe os logs se algo estiver estranho
- Configure alertas se possível

### 3. Backup regular do banco
```bash
# Backup do MongoDB
mongodump --db test_database --out /backup/$(date +%Y%m%d)

# Verificar backups
ls -lh /backup/
```

### 4. Log rotation configurado
- Logs limitados a 50MB
- Mantém últimos 5 backups
- Previne disco cheio

## 📞 Quando Pedir Ajuda

**Situações que requerem atenção:**
- ❌ Serviços ficam STOPPED por mais de 1 minuto
- ❌ Memória acima de 95%
- ❌ Disco acima de 90%
- ❌ Erros frequentes de banco de dados
- ❌ Timeout em requisições

**Logs para compartilhar:**
```bash
# Coletar todos os logs relevantes
sudo supervisorctl status > /tmp/status.txt
tail -n 100 /var/log/supervisor/backend.err.log > /tmp/backend_errors.txt
tail -n 100 /var/log/supervisor/frontend.err.log > /tmp/frontend_errors.txt
free -h > /tmp/memory.txt
df -h > /tmp/disk.txt
```

## 📊 Status Atual do Sistema

**Última verificação:** Novembro 2025

**Configuração:** Modo Desenvolvimento (com hot-reload)
**Status:** ✅ FUNCIONANDO (reinícios são normais em dev)
**Memória:** 17GB usado de 62GB (27% - Normal)
**Serviços:** Todos RUNNING
**MongoDB:** Ativo e estável
**Casos no sistema:** 30

**Recomendação:** Sistema está estável. Os "reinícios" são comportamento esperado do modo de desenvolvimento.

## 🎯 Conclusão

O sistema **NÃO estava caindo** - estava apenas reiniciando automaticamente devido ao hot-reload do modo de desenvolvimento. Isso é **comportamento esperado e normal**.

**Para máxima estabilidade em produção:** Use a configuração em `/app/supervisord_production.conf`

**Última atualização:** Novembro 2025
