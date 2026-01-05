#!/usr/bin/env python3
"""
Adicionar 4 casos faltantes da imagem para completar 20 casos pendentes
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import uuid
import os
import random

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'safe2go_helpdesk')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# 4 casos faltantes
CASOS_FALTANTES = [
    {
        "jira_id": "S2GSS-10786",
        "title": "Inclusão de observações",
        "responsible": "luiz filipe barreiros nunes",
        "seguradora": "ESSOR"
    },
    {
        "jira_id": "S2GSS-10785",
        "title": "URGENTE - CANCELAMENTO INDEVIDO",
        "responsible": "Yasmin Fazani Rego",
        "seguradora": "ESSOR"  # AXPERT → ESSOR
    },
    {
        "jira_id": "S2GSS-10668",
        "title": "ADEQUAÇÃO NOVA LEI DO SEGURO - Numero das cotações | preservação de cotação.",
        "responsible": "Yasmin Fazani Rego",
        "seguradora": "ESSOR"  # AXPERT → ESSOR
    },
    {
        "jira_id": "S2GSS-10660",
        "title": "COSSEGURADO INTERNACIONAL",
        "responsible": "Yasmin Fazani Rego",
        "seguradora": "ESSOR"  # AXPERT → ESSOR
    }
]

async def adicionar_casos():
    """Adiciona os 4 casos faltantes"""
    print("\n" + "="*70)
    print("📝 ADICIONANDO 4 CASOS FALTANTES")
    print("="*70)
    
    # Pegar um usuário admin como creator
    admin_user = await db.users.find_one({"role": "administrador"})
    creator_id = admin_user['id'] if admin_user else str(uuid.uuid4())
    
    # Data base: distribuir pelos últimos 3 dias
    hoje = datetime.utcnow()
    
    casos_adicionados = 0
    
    for i, caso_data in enumerate(CASOS_FALTANTES):
        # Verificar se já existe
        existing = await db.cases.find_one({"jira_id": caso_data["jira_id"]})
        if existing:
            print(f"  ⚠️  {caso_data['jira_id']} já existe")
            continue
        
        case_id = str(uuid.uuid4())
        
        # Distribuir ao longo dos últimos 3 dias
        dias_atras = random.randint(1, 3)
        hora = random.randint(8, 18)
        minuto = random.randint(0, 59)
        
        created_date = hoje - timedelta(days=dias_atras)
        created_date = created_date.replace(hour=hora, minute=minuto, second=0, microsecond=0)
        
        caso = {
            "id": case_id,
            "jira_id": caso_data["jira_id"],
            "title": caso_data["title"],
            "description": f"Caso importado do Jira - {caso_data['title']}",
            "status": "Pendente",
            "priority": "Alta" if "URGENTE" in caso_data["title"] else "Média",
            "category": "Suporte",
            "seguradora": caso_data["seguradora"],
            "responsible": caso_data["responsible"],
            "creator_id": creator_id,
            "created_at": created_date.isoformat() + "Z",
            "updated_at": created_date.isoformat() + "Z"
        }
        
        await db.cases.insert_one(caso)
        casos_adicionados += 1
        print(f"  ✅ {caso_data['jira_id']} - {caso_data['title'][:50]}...")
    
    print("\n" + "="*70)
    print(f"✅ {casos_adicionados} CASOS ADICIONADOS COM SUCESSO!")
    print("="*70)
    
    return casos_adicionados

async def mostrar_resumo():
    """Mostra resumo final"""
    print("\n" + "="*70)
    print("📊 RESUMO FINAL")
    print("="*70)
    
    total_cases = await db.cases.count_documents({})
    pendentes = await db.cases.count_documents({"status": "Pendente"})
    
    # Casos do Jira
    jira_cases = await db.cases.count_documents({"jira_id": {"$regex": "^S2GSS-"}})
    
    print(f"\n  📊 CASOS NO SISTEMA:")
    print(f"    • Total: {total_cases}")
    print(f"    • Pendentes: {pendentes}")
    print(f"    • Casos do Jira (S2GSS-*): {jira_cases}")
    
    # Verificar os 20 casos da imagem
    ids_imagem = [
        'S2GSS-10782', 'S2GSS-10779', 'S2GSS-10778', 'S2GSS-10746', 'S2GSS-10737',
        'S2GSS-10723', 'S2GSS-10786', 'S2GSS-10750', 'S2GSS-10728', 'S2GSS-10785',
        'S2GSS-10774', 'S2GSS-10743', 'S2GSS-10740', 'S2GSS-10702', 'S2GSS-10668',
        'S2GSS-10660', 'S2GSS-10524', 'S2GSS-10437', 'S2GSS-9650', 'S2GSS-8419'
    ]
    
    encontrados = 0
    for jira_id in ids_imagem:
        caso = await db.cases.find_one({"jira_id": jira_id})
        if caso:
            encontrados += 1
    
    print(f"\n  ✅ CASOS DA IMAGEM NO SISTEMA: {encontrados}/20")
    
    if encontrados == 20:
        print("\n  🎉 TODOS OS 20 CASOS DA IMAGEM ESTÃO NO SISTEMA!")
    
    print("\n" + "="*70 + "\n")

async def main():
    print("\n" + "="*70)
    print("🚀 COMPLETANDO CASOS PENDENTES PARA 20")
    print("="*70)
    
    # Adicionar casos faltantes
    await adicionar_casos()
    
    # Mostrar resumo
    await mostrar_resumo()

if __name__ == "__main__":
    asyncio.run(main())
