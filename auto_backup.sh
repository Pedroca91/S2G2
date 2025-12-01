#!/bin/bash
# Script de Backup Automático
# Execute este script periodicamente (ex: cron job)

echo "🤖 Iniciando backup automático..."
echo "📅 Data: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

cd /app

# Fazer backup
python backup_mongodb.py

# Manter apenas os últimos 10 backups (para economizar espaço)
echo ""
echo "🧹 Limpando backups antigos..."

cd backups
BACKUP_COUNT=$(ls -d backup_* 2>/dev/null | wc -l)

if [ $BACKUP_COUNT -gt 10 ]; then
    echo "📊 Encontrados $BACKUP_COUNT backups"
    echo "🗑️  Removendo os mais antigos (mantendo 10)..."
    
    ls -dt backup_* | tail -n +11 | xargs rm -rf
    
    echo "✅ Limpeza concluída!"
else
    echo "✅ Total de backups: $BACKUP_COUNT (OK)"
fi

echo ""
echo "🎉 Backup automático concluído!"
