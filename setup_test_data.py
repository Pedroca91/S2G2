#!/usr/bin/env python3
"""
Setup test data for Safe2Go Helpdesk System
Creates admin and client users with known credentials
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

async def setup_test_data():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔧 Setting up test data for Safe2Go Helpdesk...")
    
    # Check if users already exist
    existing_admin = await db.users.find_one({'email': 'pedro.carvalho@safe2go.com.br'})
    existing_client = await db.users.find_one({'email': 'cliente@teste.com'})
    
    if existing_admin:
        print("✅ Admin user already exists")
    else:
        # Create admin user
        admin_user = {
            'id': str(uuid.uuid4()),
            'name': 'Pedro Carvalho',
            'email': 'pedro.carvalho@safe2go.com.br',
            'password': hash_password('senha123'),
            'role': 'administrador',
            'status': 'aprovado',
            'phone': '+55 11 99999-9999',
            'company': 'Safe2Go',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'approved_at': datetime.now(timezone.utc).isoformat(),
            'approved_by': 'system'
        }
        await db.users.insert_one(admin_user)
        print("✅ Created admin user: pedro.carvalho@safe2go.com.br (senha: senha123)")
    
    if existing_client:
        print("✅ Client user already exists")
    else:
        # Create client user
        client_user = {
            'id': str(uuid.uuid4()),
            'name': 'Cliente Teste',
            'email': 'cliente@teste.com',
            'password': hash_password('senha123'),
            'role': 'cliente',
            'status': 'aprovado',
            'phone': '+55 11 88888-8888',
            'company': 'Empresa Teste',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'approved_at': datetime.now(timezone.utc).isoformat(),
            'approved_by': 'system'
        }
        await db.users.insert_one(client_user)
        print("✅ Created client user: cliente@teste.com (senha: senha123)")
    
    # Create some sample cases
    admin_user_doc = await db.users.find_one({'email': 'pedro.carvalho@safe2go.com.br'})
    client_user_doc = await db.users.find_one({'email': 'cliente@teste.com'})
    
    existing_cases = await db.cases.count_documents({})
    if existing_cases == 0:
        # Create sample cases
        sample_cases = [
            {
                'id': str(uuid.uuid4()),
                'jira_id': 'S2GSS-00001',
                'title': 'Problema com integração AVLA',
                'description': 'Sistema não está sincronizando dados com a seguradora AVLA',
                'responsible': 'Pedro Carvalho',
                'creator_id': client_user_doc['id'],
                'creator_name': client_user_doc['name'],
                'status': 'Pendente',
                'priority': 'Alta',
                'seguradora': 'AVLA',
                'category': 'Integração',
                'keywords': ['avla', 'integração', 'sincronização'],
                'opened_date': datetime.now(timezone.utc).isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'id': str(uuid.uuid4()),
                'jira_id': 'S2GSS-00002',
                'title': 'Erro no processamento de boletos',
                'description': 'Boletos não estão sendo gerados corretamente para clientes ESSOR',
                'responsible': 'Equipe Suporte',
                'creator_id': client_user_doc['id'],
                'creator_name': client_user_doc['name'],
                'status': 'Aguardando resposta do cliente',
                'priority': 'Média',
                'seguradora': 'ESSOR',
                'category': 'Erro Boleto',
                'keywords': ['boleto', 'essor', 'pagamento'],
                'opened_date': datetime.now(timezone.utc).isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        for case in sample_cases:
            await db.cases.insert_one(case)
        
        print(f"✅ Created {len(sample_cases)} sample cases")
    else:
        print(f"✅ Found {existing_cases} existing cases")
    
    # Create sample notifications
    existing_notifications = await db.notifications.count_documents({})
    if existing_notifications == 0:
        sample_notifications = [
            {
                'id': str(uuid.uuid4()),
                'user_id': client_user_doc['id'],
                'case_id': 'S2GSS-00001',
                'case_title': 'Problema com integração AVLA',
                'message': 'Seu chamado foi atribuído ao responsável Pedro Carvalho',
                'type': 'case_assigned',
                'read': False,
                'created_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'id': str(uuid.uuid4()),
                'user_id': admin_user_doc['id'],
                'case_id': 'S2GSS-00002',
                'case_title': 'Erro no processamento de boletos',
                'message': 'Novo chamado criado pelo cliente',
                'type': 'new_case',
                'read': False,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        for notification in sample_notifications:
            await db.notifications.insert_one(notification)
        
        print(f"✅ Created {len(sample_notifications)} sample notifications")
    else:
        print(f"✅ Found {existing_notifications} existing notifications")
    
    client.close()
    print("\n🎉 Test data setup complete!")
    print("\nTest Credentials:")
    print("  Admin: pedro.carvalho@safe2go.com.br / senha123")
    print("  Client: cliente@teste.com / senha123")

if __name__ == "__main__":
    asyncio.run(setup_test_data())