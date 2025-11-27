#!/usr/bin/env python3
"""
Criar usuário admin: pedro.carvalho@fase2go.com.br
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

async def create_admin():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔧 Criando usuário administrador...")
    
    # Check if user already exists
    existing_user = await db.users.find_one({'email': 'pedro.carvalho@fase2go.com.br'})
    
    if existing_user:
        print("⚠️  Usuário já existe. Atualizando senha e garantindo role admin...")
        
        # Update existing user
        await db.users.update_one(
            {'email': 'pedro.carvalho@fase2go.com.br'},
            {
                '$set': {
                    'password': hash_password('S@muka91'),
                    'role': 'administrador',
                    'status': 'aprovado',
                    'approved_at': datetime.now(timezone.utc).isoformat(),
                    'approved_by': 'system'
                }
            }
        )
        print("✅ Usuário atualizado com sucesso!")
    else:
        # Create new admin user
        admin_user = {
            'id': str(uuid.uuid4()),
            'name': 'Pedro Carvalho',
            'email': 'pedro.carvalho@fase2go.com.br',
            'password': hash_password('S@muka91'),
            'role': 'administrador',
            'status': 'aprovado',
            'phone': None,
            'company': 'Fase2Go',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'approved_at': datetime.now(timezone.utc).isoformat(),
            'approved_by': 'system'
        }
        await db.users.insert_one(admin_user)
        print("✅ Usuário administrador criado com sucesso!")
    
    client.close()
    print("\n📧 Email: pedro.carvalho@fase2go.com.br")
    print("🔑 Senha: S@muka91")
    print("👤 Role: administrador")
    print("✅ Status: aprovado")

if __name__ == "__main__":
    asyncio.run(create_admin())
