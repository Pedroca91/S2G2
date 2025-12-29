#!/usr/bin/env python3
"""
Criar usuário administrador com email pedrohcarvalho1997@gmail.com
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from passlib.context import CryptContext
import uuid
import os

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'safe2go_helpdesk')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def criar_usuario():
    # Verificar se já existe
    existing = await db.users.find_one({"email": "pedrohcarvalho1997@gmail.com"})
    if existing:
        print("❌ Usuário já existe!")
        print(f"Nome: {existing['name']}")
        print(f"Email: {existing['email']}")
        print(f"Role: {existing['role']}")
        return
    
    # Criar novo usuário
    user_id = str(uuid.uuid4())
    senha = "S@muka91"  # Mesma senha dos outros admins
    
    usuario = {
        "id": user_id,
        "name": "Pedro Carvalho",
        "email": "pedrohcarvalho1997@gmail.com",
        "password": pwd_context.hash(senha),
        "role": "administrador",
        "status": "aprovado",
        "phone": "11987654321",
        "company": "Safe2Go",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "approved_at": datetime.utcnow().isoformat() + "Z",
        "approved_by": "system"
    }
    
    await db.users.insert_one(usuario)
    
    print("="*60)
    print("✅ USUÁRIO CRIADO COM SUCESSO!")
    print("="*60)
    print(f"\n📧 Email: pedrohcarvalho1997@gmail.com")
    print(f"🔑 Senha: {senha}")
    print(f"👤 Nome: Pedro Carvalho")
    print(f"🎯 Role: administrador")
    print(f"✅ Status: aprovado")
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(criar_usuario())
