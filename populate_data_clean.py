#!/usr/bin/env python3
"""
Script para popular o banco de dados Safe2Go apenas com seguradoras válidas:
AVLA, ESSOR e Daycoval
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path
from dotenv import load_dotenv
import uuid
from datetime import datetime, timedelta, timezone
import random

# Load environment
ROOT_DIR = Path('backend')
load_dotenv(ROOT_DIR / '.env')

RESPONSAVEIS = [
    "Pedro Carvalho",
    "Ana Silva",
    "Carlos Santos",
    "Maria Oliveira",
    "João Souza"
]

CATEGORIAS = [
    "Técnico",
    "Funcional",
    "Performance",
    "Interface",
    "Integração"
]

async def populate_database():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 80)
    print("🚀 POPULANDO BANCO DE DADOS SAFE2GO (SEGURADORAS: AVLA, ESSOR, DAYCOVAL)")
    print("=" * 80)
    
    # Buscar usuário admin para usar como creator
    admin_user = await db.users.find_one({'role': 'administrador'})
    if not admin_user:
        print("❌ Nenhum usuário admin encontrado. Execute create_admin_pedro.py primeiro.")
        return
    
    creator_id = admin_user['id']
    print(f"✅ Usuário admin encontrado: {admin_user['email']}")
    
    # Limpar casos existentes
    await db.cases.delete_many({})
    print(f"✅ Banco limpo.")
    
    # Inserir casos distribuídos
    print("\n📊 INSERINDO CASOS...")
    print("-" * 80)
    
    # Definir período (últimos 7 dias)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=6)
    
    # Distribuir casos: 25 para cada seguradora (75 total)
    # 15 concluídos + 10 pendentes por seguradora
    seguradoras = ["AVLA", "ESSOR", "DAYCOVAL"]
    
    total_casos = 0
    for seguradora in seguradoras:
        print(f"\n  📌 {seguradora}:")
        
        # 15 concluídos
        for i in range(15):
            random_date = start_date + timedelta(
                days=random.randint(0, 6),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            caso = {
                "id": str(uuid.uuid4()),
                "jira_id": f"SGSS-{seguradora[:3].upper()}-{str(total_casos + 1).zfill(3)}",
                "title": f"Chamado {seguradora} #{i+1} - {random.choice(['Integração', 'Performance', 'Bug', 'Melhoria'])}",
                "description": f"Descrição detalhada do chamado para seguradora {seguradora}. " + 
                              f"Categoria: {random.choice(CATEGORIAS)}",
                "status": "Concluído",
                "responsible": random.choice(RESPONSAVEIS),
                "seguradora": seguradora,
                "category": random.choice(CATEGORIAS),
                "priority": random.choice(["Alta", "Média", "Baixa"]),
                "creator_id": creator_id,
                "created_at": random_date.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "closed_date": (random_date + timedelta(hours=random.randint(1, 72))).isoformat()
            }
            
            await db.cases.insert_one(caso)
            total_casos += 1
        
        # 10 pendentes
        for i in range(10):
            random_date = start_date + timedelta(
                days=random.randint(0, 6),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            caso = {
                "id": str(uuid.uuid4()),
                "jira_id": f"SGSS-{seguradora[:3].upper()}-{str(total_casos + 1).zfill(3)}",
                "title": f"Chamado {seguradora} #{i+16} - {random.choice(['Análise', 'Desenvolvimento', 'Teste', 'Deploy'])}",
                "description": f"Descrição detalhada do chamado pendente para seguradora {seguradora}. " + 
                              f"Categoria: {random.choice(CATEGORIAS)}",
                "status": random.choice(["Pendente", "Em Desenvolvimento", "Aguardando resposta"]),
                "responsible": random.choice(RESPONSAVEIS),
                "seguradora": seguradora,
                "category": random.choice(CATEGORIAS),
                "priority": random.choice(["Alta", "Média", "Baixa"]),
                "creator_id": creator_id,
                "created_at": random_date.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.cases.insert_one(caso)
            total_casos += 1
        
        print(f"    ✅ 25 casos inseridos ({seguradora})")
    
    # Resumo final
    print("\n" + "=" * 80)
    print("📊 RESUMO DA POPULAÇÃO DE DADOS")
    print("=" * 80)
    
    total = await db.cases.count_documents({})
    pendentes = await db.cases.count_documents({"status": {"$in": ["Pendente", "Em Desenvolvimento", "Aguardando resposta"]}})
    concluidos = await db.cases.count_documents({"status": "Concluído"})
    
    print(f"\n  📈 Total de casos no banco: {total}")
    print(f"  🟡 Pendentes/Em Desenvolvimento/Aguardando: {pendentes}")
    print(f"  🟢 Concluídos: {concluidos}")
    
    # Distribuição por seguradora
    print(f"\n  📊 Casos por seguradora:")
    for seg in seguradoras:
        count = await db.cases.count_documents({"seguradora": seg})
        print(f"    • {seg}: {count} casos")
    
    completion_rate = round((concluidos / total * 100), 1) if total > 0 else 0
    print(f"\n  ✅ Taxa de conclusão: {completion_rate}%")
    
    print("\n✅ POPULAÇÃO DE DADOS CONCLUÍDA COM SUCESSO!")
    print("=" * 80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(populate_database())
