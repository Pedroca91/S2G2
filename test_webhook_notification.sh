#!/bin/bash

echo "🧪 Testando Webhook → WebSocket → Notificação"
echo "=============================================="
echo ""

# Simular webhook do Jira
echo "1️⃣ Enviando webhook do Jira..."
curl -X POST "http://localhost:8001/api/webhooks/jira" \
  -H "Content-Type: application/json" \
  -d '{
    "webhookEvent": "jira:issue_created",
    "issue": {
      "key": "S2GSS-TEST-001",
      "fields": {
        "summary": "Teste de Notificação Sonora",
        "description": "Este é um teste para verificar se o som está tocando",
        "assignee": {
          "displayName": "Pedro AVLA"
        },
        "status": {
          "name": "To Do"
        }
      }
    }
  }' 2>/dev/null

echo ""
echo ""
echo "2️⃣ Verificando logs do backend..."
echo ""
tail -n 20 /var/log/supervisor/backend.out.log | grep -E "(webhook|WebSocket|broadcast)" | tail -10

echo ""
echo "=============================================="
echo "✅ Teste concluído!"
echo ""
echo "📋 O que verificar no navegador:"
echo "  1. Abra a página de Casos"
echo "  2. Verifique se aparece '🟢 Ao vivo'"
echo "  3. Se aparecer '🔔 Ativar Som', clique nele"
echo "  4. Execute este script novamente"
echo "  5. Você deve ouvir o som 'ding-dong'"
echo ""
