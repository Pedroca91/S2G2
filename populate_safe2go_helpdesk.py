#!/usr/bin/env python3
"""
Script para popular o banco SAFE2GO_HELPDESK (nome correto do banco)
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import random
from passlib.context import CryptContext
import uuid
import os

# Usar o mesmo banco que o backend
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'safe2go_helpdesk')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SEGURADORAS = ["AVLA", "ESSOR", "DAYCOVAL"]
CATEGORIAS = ["Interface", "Técnico", "Integração", "Performance", "Funcional", "Suporte", "Configuração", "Bug", "Melhoria"]
STATUS_OPTIONS = ["Pendente", "Em Desenvolvimento", "Aguardando resposta", "Concluído"]
PRIORIDADES = ["Baixa", "Média", "Alta", "Crítica"]

NOMES_ADMINS = [
    ("Pedro Carvalho", "pedro.carvalho@safe2go.com.br", "11987654321"),
    ("Maria Silva", "maria.silva@safe2go.com.br", "11987654322"),
    ("João Santos", "joao.santos@safe2go.com.br", "11987654323"),
    ("Ana Costa", "ana.costa@safe2go.com.br", "11987654324")
]

NOMES_CLIENTES = [
    ("Carlos Oliveira", "carlos.oliveira@avla.com.br", "11987651111", "AVLA"),
    ("Juliana Lima", "juliana.lima@avla.com.br", "11987651112", "AVLA"),
    ("Roberto Ferreira", "roberto.ferreira@avla.com.br", "11987651113", "AVLA"),
    ("Patrícia Souza", "patricia.souza@essor.com.br", "11987652221", "ESSOR"),
    ("Fernando Alves", "fernando.alves@essor.com.br", "11987652222", "ESSOR"),
    ("Luciana Martins", "luciana.martins@essor.com.br", "11987652223", "ESSOR"),
    ("Ricardo Pereira", "ricardo.pereira@daycoval.com.br", "11987653331", "DAYCOVAL"),
    ("Camila Rodrigues", "camila.rodrigues@daycoval.com.br", "11987653332", "DAYCOVAL"),
    ("Bruno Nascimento", "bruno.nascimento@daycoval.com.br", "11987653333", "DAYCOVAL")
]

RESPONSAVEIS = [
    "Pedro Carvalho", "Maria Silva", "João Santos", "Ana Costa",
    "Equipe Técnica", "Suporte Nível 1", "Suporte Nível 2"
]

async def limpar_banco():
    """Limpa todos os dados do banco"""
    print(f"\n🗑️  LIMPANDO BANCO: {DB_NAME}")
    await db.users.delete_many({})
    await db.cases.delete_many({})
    await db.comments.delete_many({})
    await db.notifications.delete_many({})
    await db.activities.delete_many({})
    print("    ✅ Banco limpo")

async def criar_usuarios():
    print("\n👥 CRIANDO USUÁRIOS...")
    usuarios_criados = []
    senha_padrao = "S@muka91"
    senha_cliente = "senha123"
    
    for nome, email, telefone in NOMES_ADMINS:
        user_id = str(uuid.uuid4())
        usuario = {
            "id": user_id,
            "name": nome,
            "email": email,
            "password": pwd_context.hash(senha_padrao),
            "role": "administrador",
            "status": "aprovado",
            "phone": telefone,
            "company": "Safe2Go",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "approved_at": datetime.utcnow().isoformat() + "Z",
            "approved_by": "system"
        }
        await db.users.insert_one(usuario)
        usuarios_criados.append(user_id)
        print(f"    ✅ {nome}")
    
    for nome, email, telefone, seguradora in NOMES_CLIENTES:
        user_id = str(uuid.uuid4())
        usuario = {
            "id": user_id,
            "name": nome,
            "email": email,
            "password": pwd_context.hash(senha_cliente),
            "role": "cliente",
            "status": "aprovado",
            "phone": telefone,
            "company": seguradora,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "approved_at": datetime.utcnow().isoformat() + "Z",
            "approved_by": "system"
        }
        await db.users.insert_one(usuario)
        usuarios_criados.append(user_id)
        print(f"    ✅ {nome} ({seguradora})")
    
    return usuarios_criados

async def criar_casos(usuarios_ids):
    print("\n📊 CRIANDO 75 CASOS...")
    casos_criados = []
    caso_numero = 1
    data_base = datetime.utcnow() - timedelta(days=7)
    
    for seguradora in SEGURADORAS:
        for i in range(25):
            case_id = str(uuid.uuid4())
            if i < 15:
                status = "Concluído"
            else:
                status = random.choice(["Pendente", "Em Desenvolvimento", "Aguardando resposta"])
            
            dias_atras = random.randint(0, 7)
            data_criacao = data_base + timedelta(days=dias_atras, hours=random.randint(0, 23))
            
            caso = {
                "id": case_id,
                "jira_id": f"SGSS-N{caso_numero:03d}",
                "title": f"Caso {caso_numero} - {random.choice(['Suporte técnico', 'Dúvida sistema', 'Erro integração', 'Atualização cadastro'])}",
                "description": f"Descrição do caso {caso_numero} para {seguradora}.",
                "status": status,
                "priority": random.choice(PRIORIDADES),
                "category": random.choice(CATEGORIAS),
                "seguradora": seguradora,
                "responsible": random.choice(RESPONSAVEIS),
                "creator_id": random.choice(usuarios_ids),
                "created_at": data_criacao.isoformat() + "Z",
                "updated_at": (data_criacao + timedelta(hours=random.randint(1, 48))).isoformat() + "Z"
            }
            
            if status == "Concluído":
                caso["completed_at"] = (data_criacao + timedelta(days=random.randint(1, 3))).isoformat() + "Z"
            
            await db.cases.insert_one(caso)
            casos_criados.append(case_id)
            caso_numero += 1
        
        print(f"    ✅ 25 casos {seguradora}")
    
    return casos_criados

async def criar_comentarios(casos_ids, usuarios_ids):
    print("\n💬 CRIANDO COMENTÁRIOS...")
    comentarios = [
        "Estou analisando o caso.",
        "Solução aplicada e testada.",
        "Aguardando retorno do cliente.",
        "Caso resolvido com sucesso."
    ]
    
    total = 0
    casos_com_comentarios = random.sample(casos_ids, k=len(casos_ids)//2)
    
    for case_id in casos_com_comentarios:
        for i in range(random.randint(1, 3)):
            comment_id = str(uuid.uuid4())
            await db.comments.insert_one({
                "id": comment_id,
                "case_id": case_id,
                "user_id": random.choice(usuarios_ids),
                "content": random.choice(comentarios),
                "is_internal": random.choice([True, False]),
                "created_at": (datetime.utcnow() - timedelta(hours=random.randint(1, 72))).isoformat() + "Z"
            })
            total += 1
    
    print(f"    ✅ {total} comentários criados")
    return total

async def criar_notificacoes(usuarios_ids):
    print("\n🔔 CRIANDO NOTIFICAÇÕES...")
    mensagens = [
        ("Novo caso atribuído", "case_assigned"),
        ("Comentário adicionado", "comment_added"),
        ("Status atualizado", "case_updated")
    ]
    
    total = 0
    for user_id in usuarios_ids:
        for i in range(random.randint(2, 4)):
            notif_id = str(uuid.uuid4())
            msg, tipo = random.choice(mensagens)
            is_read = random.random() < 0.3
            
            notif = {
                "id": notif_id,
                "user_id": user_id,
                "message": msg,
                "type": tipo,
                "is_read": is_read,
                "created_at": (datetime.utcnow() - timedelta(hours=random.randint(1, 168))).isoformat() + "Z"
            }
            
            if is_read:
                notif["read_at"] = (datetime.utcnow() - timedelta(hours=random.randint(0, 24))).isoformat() + "Z"
            
            await db.notifications.insert_one(notif)
            total += 1
    
    print(f"    ✅ {total} notificações criadas")
    return total

async def criar_atividades(casos_ids, usuarios_ids):
    print("\n📝 CRIANDO ATIVIDADES...")
    tipos = ["case_created", "case_updated", "comment_added"]
    
    total = 0
    for case_id in casos_ids:
        for i in range(random.randint(1, 2)):
            activity_id = str(uuid.uuid4())
            await db.activities.insert_one({
                "id": activity_id,
                "case_id": case_id,
                "user_id": random.choice(usuarios_ids),
                "action": random.choice(tipos),
                "details": "Atividade registrada",
                "created_at": (datetime.utcnow() - timedelta(hours=random.randint(1, 168))).isoformat() + "Z"
            })
            total += 1
    
    print(f"    ✅ {total} atividades criadas")
    return total

async def mostrar_resumo():
    print("\n" + "="*80)
    print(f"📊 RESUMO - Banco: {DB_NAME}")
    print("="*80)
    
    total_users = await db.users.count_documents({})
    total_admins = await db.users.count_documents({"role": "administrador"})
    total_clients = await db.users.count_documents({"role": "cliente"})
    total_cases = await db.cases.count_documents({})
    completed = await db.cases.count_documents({"status": "Concluído"})
    total_comments = await db.comments.count_documents({})
    total_notifications = await db.notifications.count_documents({})
    total_activities = await db.activities.count_documents({})
    
    avla = await db.cases.count_documents({"seguradora": "AVLA"})
    essor = await db.cases.count_documents({"seguradora": "ESSOR"})
    daycoval = await db.cases.count_documents({"seguradora": "DAYCOVAL"})
    
    print(f"\n  👥 USUÁRIOS: {total_users} ({total_admins} admins, {total_clients} clientes)")
    print(f"  📊 CASOS: {total_cases} ({completed} concluídos - {completed/total_cases*100:.0f}%)")
    print(f"  🏢 SEGURADORAS: AVLA({avla}), ESSOR({essor}), DAYCOVAL({daycoval})")
    print(f"  💬 COMENTÁRIOS: {total_comments}")
    print(f"  🔔 NOTIFICAÇÕES: {total_notifications}")
    print(f"  📝 ATIVIDADES: {total_activities}")
    
    print("\n  📋 CREDENCIAIS:")
    print("    Admin: pedro.carvalho@safe2go.com.br / S@muka91")
    print("    Cliente: carlos.oliveira@avla.com.br / senha123")
    print("\n" + "="*80)
    print("✅ SISTEMA PRONTO!")
    print("="*80 + "\n")

async def main():
    print("\n" + "="*80)
    print(f"🚀 POPULANDO SISTEMA SAFE2GO - Banco: {DB_NAME}")
    print("="*80)
    
    await limpar_banco()
    usuarios_ids = await criar_usuarios()
    casos_ids = await criar_casos(usuarios_ids)
    await criar_comentarios(casos_ids, usuarios_ids)
    await criar_notificacoes(usuarios_ids)
    await criar_atividades(casos_ids, usuarios_ids)
    await mostrar_resumo()

if __name__ == "__main__":
    asyncio.run(main())
