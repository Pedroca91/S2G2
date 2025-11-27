#!/usr/bin/env python3
"""
Script para atualizar Pedro Carvalho como administrador
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

async def update_pedro():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Atualizar Pedro Carvalho
    result = await db.users.update_one(
        {'email': 'pedro.carvalho@safe2go.com.br'},
        {
            '$set': {
                'role': 'administrador',
                'status': 'aprovado',
                'approved_at': datetime.now(timezone.utc).isoformat(),
                'approved_by': 'sistema'
            }
        }
    )
    
    if result.modified_count > 0:
        print("✅ Pedro Carvalho atualizado para Administrador!")
        
        user = await db.users.find_one(
            {'email': 'pedro.carvalho@safe2go.com.br'},
            {'_id': 0, 'password': 0}
        )
        print(f"\n📋 Dados:")
        print(f"   Nome: {user.get('name')}")
        print(f"   Email: {user.get('email')}")
        print(f"   Role: {user.get('role')}")
        print(f"   Status: {user.get('status')}")
    else:
        print("⚠️ Usuário não encontrado ou já estava atualizado")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(update_pedro())
