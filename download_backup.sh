#!/bin/bash
# Script para preparar backup para download
# Comprime o backup mais recente em um arquivo .tar.gz

echo "📦 Preparando backup para download..."
echo ""

cd /app/backups

# Encontrar o backup mais recente
LATEST_BACKUP=$(ls -dt backup_* 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ Nenhum backup encontrado!"
    exit 1
fi

echo "📂 Backup mais recente: $LATEST_BACKUP"
echo ""

# Nome do arquivo comprimido
COMPRESSED_FILE="${LATEST_BACKUP}.tar.gz"

# Comprimir
echo "🗜️  Comprimindo..."
tar -czf "$COMPRESSED_FILE" "$LATEST_BACKUP/"

# Informações
FILE_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
echo ""
echo "✅ Backup comprimido com sucesso!"
echo "📁 Arquivo: backups/$COMPRESSED_FILE"
echo "💾 Tamanho: $FILE_SIZE"
echo ""
echo "💡 Você pode baixar este arquivo pela interface da Emergent:"
echo "   Files → backups → $COMPRESSED_FILE"
echo ""
echo "🔓 Para descomprimir em sua máquina:"
echo "   tar -xzf $COMPRESSED_FILE"
