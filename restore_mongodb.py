#!/usr/bin/env python3
"""
Script de Restore do MongoDB
Importa dados de backup JSON para o banco
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment
ROOT_DIR = Path('backend')
load_dotenv(ROOT_DIR / '.env')

async def restore_collection(db, collection_name, file_path):
    """Restaura uma coleção de um arquivo JSON"""
    try:
        print(f"📥 Restaurando: {collection_name}")
        
        # Ler arquivo JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        if not documents:
            print(f"  ⚠️  Arquivo vazio, pulando...")
            return
        
        print(f"  📊 {len(documents)} documentos encontrados")
        
        collection = db[collection_name]
        
        # Limpar coleção existente (CUIDADO!)
        deleted = await collection.delete_many({})
        if deleted.deleted_count > 0:
            print(f"  🗑️  Removidos {deleted.deleted_count} documentos antigos")
        
        # Inserir documentos
        if documents:
            # Converter strings ISO para datetime
            for doc in documents:
                for key, value in doc.items():
                    if isinstance(value, str) and 'T' in value and ':' in value:
                        try:
                            doc[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except:
                            pass
            
            result = await collection.insert_many(documents)
            print(f"  ✅ Inseridos {len(result.inserted_ids)} documentos")
        
    except Exception as e:
        print(f"  ❌ Erro ao restaurar {collection_name}: {e}")

async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("❌ Uso: python restore_mongodb.py <pasta_backup>")
        print("\nExemplo:")
        print("  python restore_mongodb.py backups/backup_20251127_180530")
        
        # Listar backups disponíveis
        backup_dir = Path('backups')
        if backup_dir.exists():
            backups = sorted([d for d in backup_dir.iterdir() if d.is_dir()], reverse=True)
            if backups:
                print("\n📂 Backups disponíveis:")
                for backup in backups[:5]:
                    print(f"  - {backup.name}")
        return
    
    backup_path = Path(sys.argv[1])
    
    if not backup_path.exists():
        print(f"❌ Pasta não encontrada: {backup_path}")
        return
    
    # Ler metadata
    metadata_path = backup_path / 'metadata.json'
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            print(f"📅 Backup de: {metadata.get('backup_date')}")
            print(f"🗄️  Banco: {metadata.get('database_name')}\n")
    
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    print("🔧 Conectando ao MongoDB...")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("⚠️  ATENÇÃO: Os dados existentes serão SUBSTITUÍDOS!")
    response = input("Deseja continuar? (sim/não): ")
    
    if response.lower() not in ['sim', 's', 'yes', 'y']:
        print("❌ Operação cancelada")
        return
    
    print(f"\n🔄 Restaurando de: {backup_path}\n")
    
    # Encontrar todos os arquivos JSON
    json_files = list(backup_path.glob('*.json'))
    json_files = [f for f in json_files if f.name != 'metadata.json']
    
    if not json_files:
        print("❌ Nenhum arquivo de backup encontrado!")
        return
    
    print(f"📋 Arquivos encontrados: {len(json_files)}\n")
    
    # Restaurar cada coleção
    for json_file in json_files:
        collection_name = json_file.stem
        await restore_collection(db, collection_name, json_file)
        print()
    
    print("🎉 Restore concluído com sucesso!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
