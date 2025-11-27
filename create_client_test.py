#!/usr/bin/env python3
"""
Criar usuário cliente de teste com seguradora
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path
from dotenv import load_dotenv
import bcrypt
import uuid
from datetime import datetime, timezone

# Load environment
ROOT_DIR = Path('backend')
load_dotenv(ROOT_DIR / '.env')

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

async def create_client():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔧 Criando usuário cliente de teste...")
    
    # Check if user already exists
    existing_user = await db.users.find_one({'email': 'cliente@avla.com.br'})
    
    if existing_user:
        print("⚠️  Usuário já existe. Atualizando dados...")
        
        # Update existing user
        await db.users.update_one(
            {'email': 'cliente@avla.com.br'},
            {
                '$set': {
                    'password': hash_password('senha123'),
                    'role': 'cliente',
                    'status': 'aprovado',
                    'company': 'AVLA',
                    'approved_at': datetime.now(timezone.utc).isoformat(),
                    'approved_by': 'system'
                }
            }
        )
        print("✅ Usuário atualizado com sucesso!")
    else:
        # Create new client user
        client_user = {
            'id': str(uuid.uuid4()),
            'name': 'Cliente AVLA',
            'email': 'cliente@avla.com.br',
            'password': hash_password('senha123'),
            'role': 'cliente',
            'status': 'aprovado',
            'phone': '+55 11 77777-7777',
            'company': 'AVLA',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'approved_at': datetime.now(timezone.utc).isoformat(),
            'approved_by': 'system'
        }
        await db.users.insert_one(client_user)
        print("✅ Usuário cliente criado com sucesso!")
    
    client.close()
    print("\n📧 Email: cliente@avla.com.br")
    print("🔑 Senha: senha123")
    print("👤 Role: cliente")
    print("🏢 Seguradora: AVLA")
    print("✅ Status: aprovado")

if __name__ == "__main__":
    asyncio.run(create_client())
