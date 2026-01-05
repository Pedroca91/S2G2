#!/usr/bin/env python3
"""
Script para redistribuir datas dos casos ao longo da última semana
para criar um gráfico mais movimentado no dashboard
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import random
import os

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'safe2go_helpdesk')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

async def redistribuir_casos():
    """Redistribui casos ao longo dos últimos 7 dias"""
    print("\n" + "="*70)
    print("📊 REDISTRIBUINDO CASOS PELA ÚLTIMA SEMANA")
    print("="*70)
    
    # Pegar todos os casos
    todos_casos = await db.cases.find({}).to_list(1000)
    total_casos = len(todos_casos)
    
    print(f"\n📋 Total de casos encontrados: {total_casos}")
    
    # Data base: 7 dias atrás
    hoje = datetime.utcnow()
    data_inicial = hoje - timedelta(days=7)
    
    # Distribuição desejada por dia (para criar movimento)
    # Dia 1 (7 dias atrás): 5 casos
    # Dia 2 (6 dias atrás): 8 casos
    # Dia 3 (5 dias atrás): 12 casos
    # Dia 4 (4 dias atrás): 15 casos (pico)
    # Dia 5 (3 dias atrás): 11 casos
    # Dia 6 (2 dias atrás): 10 casos
    # Dia 7 (ontem): 9 casos
    # Dia 8 (hoje): restante
    
    distribuicao = [5, 8, 12, 15, 11, 10, 9]
    
    # Embaralhar casos para distribuir aleatoriamente
    random.shuffle(todos_casos)
    
    casos_atualizados = 0
    indice_caso = 0
    
    print("\n📅 DISTRIBUINDO CASOS:")
    print("-" * 70)
    
    for dia_offset, quantidade in enumerate(distribuicao):
        # Calcular a data do dia
        data_dia = data_inicial + timedelta(days=dia_offset)
        data_formatada = data_dia.strftime("%d/%m/%Y")
        
        # Pegar os casos para este dia
        casos_do_dia = todos_casos[indice_caso:indice_caso + quantidade]
        
        if not casos_do_dia:
            break
        
        for caso in casos_do_dia:
            # Gerar hora aleatória no dia (entre 8h e 18h)
            hora = random.randint(8, 18)
            minuto = random.randint(0, 59)
            
            nova_data = data_dia.replace(hour=hora, minute=minuto, second=0)
            
            # Atualizar created_at e updated_at
            await db.cases.update_one(
                {"id": caso["id"]},
                {"$set": {
                    "created_at": nova_data.isoformat() + "Z",
                    "updated_at": nova_data.isoformat() + "Z"
                }}
            )
            
            casos_atualizados += 1
        
        indice_caso += quantidade
        print(f"  📆 {data_formatada}: {len(casos_do_dia)} casos distribuídos")
    
    # Distribuir casos restantes no dia de hoje
    casos_restantes = todos_casos[indice_caso:]
    if casos_restantes:
        data_hoje = hoje.strftime("%d/%m/%Y")
        for caso in casos_restantes:
            hora = random.randint(8, 18)
            minuto = random.randint(0, 59)
            
            nova_data = hoje.replace(hour=hora, minute=minuto, second=0)
            
            await db.cases.update_one(
                {"id": caso["id"]},
                {"$set": {
                    "created_at": nova_data.isoformat() + "Z",
                    "updated_at": nova_data.isoformat() + "Z"
                }}
            )
            
            casos_atualizados += 1
        
        print(f"  📆 {data_hoje}: {len(casos_restantes)} casos distribuídos")
    
    print("\n" + "-" * 70)
    print(f"✅ Total de casos atualizados: {casos_atualizados}")
    
    return casos_atualizados

async def atualizar_casos_concluidos():
    """Atualiza completed_at dos casos concluídos para datas após created_at"""
    print("\n" + "="*70)
    print("🎯 ATUALIZANDO DATAS DE CONCLUSÃO")
    print("="*70)
    
    casos_concluidos = await db.cases.find({"status": "Concluído"}).to_list(1000)
    
    print(f"\n📋 Casos concluídos encontrados: {len(casos_concluidos)}")
    
    casos_atualizados = 0
    
    for caso in casos_concluidos:
        # Pegar data de criação
        created_at = datetime.fromisoformat(caso["created_at"].replace("Z", "+00:00"))
        
        # Conclusão entre 1 a 5 dias depois da criação
        dias_ate_conclusao = random.randint(1, 5)
        horas_adicionais = random.randint(1, 10)
        
        data_conclusao = created_at + timedelta(days=dias_ate_conclusao, hours=horas_adicionais)
        
        # Atualizar completed_at
        await db.cases.update_one(
            {"id": caso["id"]},
            {"$set": {
                "completed_at": data_conclusao.isoformat() + "Z",
                "updated_at": data_conclusao.isoformat() + "Z"
            }}
        )
        
        casos_atualizados += 1
    
    print(f"✅ {casos_atualizados} casos concluídos atualizados com datas de conclusão")
    
    return casos_atualizados

async def mostrar_distribuicao():
    """Mostra a distribuição final dos casos por dia"""
    print("\n" + "="*70)
    print("📊 DISTRIBUIÇÃO FINAL POR DIA")
    print("="*70)
    
    # Pegar casos dos últimos 7 dias
    data_inicial = datetime.utcnow() - timedelta(days=7)
    
    todos_casos = await db.cases.find({}).to_list(1000)
    
    # Agrupar por dia
    casos_por_dia = {}
    
    for caso in todos_casos:
        created_at = datetime.fromisoformat(caso["created_at"].replace("Z", "+00:00"))
        
        # Se está nos últimos 7 dias
        if created_at >= data_inicial:
            data_str = created_at.strftime("%d/%m/%Y")
            
            if data_str not in casos_por_dia:
                casos_por_dia[data_str] = {
                    "total": 0,
                    "pendentes": 0,
                    "aguardando": 0,
                    "concluidos": 0
                }
            
            casos_por_dia[data_str]["total"] += 1
            
            if caso["status"] == "Pendente":
                casos_por_dia[data_str]["pendentes"] += 1
            elif caso["status"] == "Aguardando resposta":
                casos_por_dia[data_str]["aguardando"] += 1
            elif caso["status"] == "Concluído":
                casos_por_dia[data_str]["concluidos"] += 1
    
    # Mostrar distribuição
    print("\n  Data       | Total | Pendentes | Aguardando | Concluídos")
    print("-" * 70)
    
    for data in sorted(casos_por_dia.keys()):
        stats = casos_por_dia[data]
        print(f"  {data} |   {stats['total']:2d}  |     {stats['pendentes']:2d}    |     {stats['aguardando']:2d}     |     {stats['concluidos']:2d}")
    
    print("\n" + "="*70)
    print("✅ REDISTRIBUIÇÃO CONCLUÍDA!")
    print("="*70)
    
    print("\n💡 O gráfico no dashboard agora mostrará movimento ao longo da semana!")
    print("\n")

async def main():
    print("\n" + "="*70)
    print("🚀 REDISTRIBUIÇÃO DE CASOS - CRIAR GRÁFICO MOVIMENTADO")
    print("="*70)
    
    # Passo 1: Redistribuir casos pela semana
    await redistribuir_casos()
    
    # Passo 2: Atualizar datas de conclusão
    await atualizar_casos_concluidos()
    
    # Passo 3: Mostrar distribuição final
    await mostrar_distribuicao()

if __name__ == "__main__":
    asyncio.run(main())
