#!/usr/bin/env python3
"""
Adicionar casos da SEMANA PASSADA (25/11 a 01/12)
Para gerar relatório PDF com dados históricos
SEM apagar os casos existentes
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
    "Erro Corretor",
    "Técnico",
    "Funcional",
    "Performance",
    "Interface",
    "Integração"
]

async def add_last_week_cases():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 80)
    print("📅 ADICIONANDO CASOS DA SEMANA PASSADA (25/11 a 01/12)")
    print("=" * 80)
    
    # Buscar usuário admin
    admin_user = await db.users.find_one({'role': 'administrador'})
    if not admin_user:
        print("❌ Nenhum usuário admin encontrado.")
        return
    
    creator_id = admin_user['id']
    print(f"✅ Usuário admin encontrado: {admin_user['email']}")
    
    # Casos existentes
    existing_count = await db.cases.count_documents({})
    print(f"📊 Casos existentes no banco: {existing_count}")
    
    # Definir período: SEMANA PASSADA (25/11 a 01/12)
    # Usando datas fixas para ter dados históricos
    start_date = datetime(2025, 11, 25, 0, 0, 0, tzinfo=timezone.utc)
    end_date = datetime(2025, 12, 1, 23, 59, 59, tzinfo=timezone.utc)
    
    print(f"\n📅 Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
    
    # Seguradoras
    seguradoras = ["AVLA", "ESSOR", "DAYCOVAL"]
    
    print("\n📝 ADICIONANDO CASOS DA SEMANA PASSADA...")
    print("-" * 80)
    
    total_added = 0
    
    # Distribuir 60 casos ao longo da semana (7 dias)
    # ~8-9 casos por dia
    for i in range(60):
        # Distribuir uniformemente durante a semana
        day_offset = (i * 7) // 60
        hours_offset = random.randint(8, 18)  # Horário comercial
        minutes_offset = random.randint(0, 59)
        
        created_date = start_date + timedelta(
            days=day_offset,
            hours=hours_offset,
            minutes=minutes_offset
        )
        
        # Escolher seguradora (20 casos cada)
        seguradora = seguradoras[i % 3]
        
        # 80% concluídos, 20% pendentes/aguardando
        if i < 48:  # 48 concluídos
            status = "Concluído"
            closed_date = created_date + timedelta(hours=random.randint(2, 72))
        else:
            status = random.choice(["Pendente", "Em Desenvolvimento", "Aguardando resposta do cliente"])
            closed_date = None
        
        # Distribuição de categorias com peso em Erro Corretor
        if i < 20:
            category = "Erro Corretor"
        elif i < 35:
            category = "Técnico"
        elif i < 45:
            category = "Funcional"
        else:
            category = random.choice(["Performance", "Interface", "Integração"])
        
        caso = {
            "id": str(uuid.uuid4()),
            "jira_id": f"HIST-{str(total_added + 1).zfill(3)}",
            "title": f"Caso histórico {seguradora} - {category}",
            "description": f"Caso da semana passada para análise histórica. Categoria: {category}",
            "status": status,
            "responsible": random.choice(RESPONSAVEIS),
            "seguradora": seguradora,
            "category": category,
            "priority": random.choice(["Alta", "Média", "Baixa"]),
            "creator_id": creator_id,
            "created_at": created_date.isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if closed_date:
            caso["closed_date"] = closed_date.isoformat()
        
        await db.cases.insert_one(caso)
        total_added += 1
        
        if (total_added % 20) == 0:
            print(f"   ✅ {total_added} casos adicionados...")
    
    # Resumo final
    print("\n" + "=" * 80)
    print("📊 RESUMO DA ADIÇÃO")
    print("=" * 80)
    
    total_now = await db.cases.count_documents({})
    concluidos = await db.cases.count_documents({"status": "Concluído"})
    pendentes = await db.cases.count_documents({"status": "Pendente"})
    aguardando = await db.cases.count_documents({"status": "Aguardando resposta do cliente"})
    em_dev = await db.cases.count_documents({"status": "Em Desenvolvimento"})
    
    print(f"\n  ➕ Casos adicionados (semana passada): {total_added}")
    print(f"  📈 Total de casos no banco: {total_now}")
    print(f"     🟢 Concluídos: {concluidos}")
    print(f"     🟡 Pendentes: {pendentes}")
    print(f"     🔵 Em Desenvolvimento: {em_dev}")
    print(f"     🟠 Aguardando resposta do cliente: {aguardando}")
    
    # Distribuição por seguradora
    print(f"\n  📊 Casos por seguradora:")
    for seg in seguradoras:
        count = await db.cases.count_documents({"seguradora": seg})
        print(f"    • {seg}: {count} casos")
    
    # Distribuição por data (semana passada)
    print(f"\n  📅 Casos da semana passada por dia:")
    for day in range(7):
        day_start = start_date + timedelta(days=day)
        day_end = day_start + timedelta(days=1)
        count = await db.cases.count_documents({
            "created_at": {
                "$gte": day_start.isoformat(),
                "$lt": day_end.isoformat()
            }
        })
        print(f"    • {day_start.strftime('%d/%m')}: {count} casos")
    
    completion_rate = round((concluidos / total_now * 100), 1) if total_now > 0 else 0
    print(f"\n  ✅ Taxa de conclusão: {completion_rate}%")
    
    print("\n✅ ADIÇÃO DA SEMANA PASSADA CONCLUÍDA!")
    print("=" * 80)
    print("\n💡 Agora você pode gerar o PDF do dashboard para ver:")
    print("   - Gráficos da última semana (25/11 a 01/12)")
    print("   - Análise de casos recorrentes")
    print("   - Distribuição completa de dados")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_last_week_cases())
