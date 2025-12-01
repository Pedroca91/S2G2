#!/usr/bin/env python3
"""
Script de Exportação CSV
Exporta coleções do MongoDB para CSV (para análise em Excel, etc)
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import csv
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment
ROOT_DIR = Path('backend')
load_dotenv(ROOT_DIR / '.env')

# Diretório de exportações
EXPORT_DIR = Path('exports')
EXPORT_DIR.mkdir(exist_ok=True)

async def export_to_csv(db, collection_name, export_path):
    """Exporta uma coleção para CSV"""
    try:
        collection = db[collection_name]
        
        # Contar documentos
        count = await collection.count_documents({})
        print(f"  📊 {count} registros")
        
        if count == 0:
            print(f"  ⚠️  Coleção vazia, pulando...")
            return
        
        # Buscar todos os documentos
        cursor = collection.find({})
        documents = await cursor.to_list(length=None)
        
        # Converter para lista de dicts
        rows = []
        all_keys = set()
        
        for doc in documents:
            row = {}
            for key, value in doc.items():
                if key == '_id':
                    row[key] = str(value)
                elif isinstance(value, datetime):
                    row[key] = value.isoformat()
                elif isinstance(value, list):
                    row[key] = ', '.join(str(v) for v in value)
                else:
                    row[key] = value
                all_keys.add(key)
            rows.append(row)
        
        # Ordenar keys
        fieldnames = sorted(all_keys)
        
        # Escrever CSV
        file_path = export_path / f"{collection_name}.csv"
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"  ✅ Exportado para: {file_path}")
        
    except Exception as e:
        print(f"  ❌ Erro ao exportar {collection_name}: {e}")

async def main():
    import sys
    
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    print("🔧 Conectando ao MongoDB...")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Criar pasta com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_path = EXPORT_DIR / f"export_{timestamp}"
    export_path.mkdir(exist_ok=True)
    
    print(f"📊 Exportando para CSV em: {export_path}\n")
    
    # Coleções para exportar
    if len(sys.argv) > 1:
        collections = sys.argv[1:]
        print(f"📋 Coleções especificadas: {', '.join(collections)}\n")
    else:
        collections = await db.list_collection_names()
        print(f"📋 Todas as coleções: {len(collections)}\n")
    
    # Exportar cada coleção
    for collection_name in collections:
        print(f"📥 Exportando: {collection_name}")
        await export_to_csv(db, collection_name, export_path)
        print()
    
    # Estatísticas
    csv_files = list(export_path.glob('*.csv'))
    total_size = sum(f.stat().st_size for f in csv_files)
    size_mb = total_size / (1024 * 1024)
    
    print(f"🎉 Exportação concluída!")
    print(f"📂 Localização: {export_path}")
    print(f"💾 Tamanho total: {size_mb:.2f} MB")
    print(f"📊 Arquivos: {len(csv_files)}")
    print(f"\n💡 Você pode abrir estes arquivos no Excel ou Google Sheets!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
