#!/usr/bin/env python3
"""
Script para popular o banco de dados Safe2Go com TODOS os dados completos:
- Múltiplos usuários (admins e clientes de cada seguradora)
- 75 casos distribuídos
- Comentários nos casos
- Notificações para usuários
- Atividades registradas
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import random
from passlib.context import CryptContext
import uuid

# Configuração do MongoDB
MONGO_URL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URL)
db = client.helpdesk_db

# Configuração de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dados base
SEGURADORAS = ["AVLA", "ESSOR", "DAYCOVAL"]
CATEGORIAS = ["Interface", "Técnico", "Integração", "Performance", "Funcional", "Suporte", "Configuração", "Bug", "Melhoria"]
STATUS_OPTIONS = ["Pendente", "Em Desenvolvimento", "Aguardando resposta", "Concluído"]
PRIORIDADES = ["Baixa", "Média", "Alta", "Crítica"]

# Nomes para usuários
NOMES_ADMINS = [
    ("Pedro Carvalho", "pedro.carvalho@safe2go.com.br", "11987654321"),
    ("Maria Silva", "maria.silva@safe2go.com.br", "11987654322"),
    ("João Santos", "joao.santos@safe2go.com.br", "11987654323"),
    ("Ana Costa", "ana.costa@safe2go.com.br", "11987654324")
]

NOMES_CLIENTES = [
    # AVLA
    ("Carlos Oliveira", "carlos.oliveira@avla.com.br", "11987651111", "AVLA"),
    ("Juliana Lima", "juliana.lima@avla.com.br", "11987651112", "AVLA"),
    ("Roberto Ferreira", "roberto.ferreira@avla.com.br", "11987651113", "AVLA"),
    
    # ESSOR
    ("Patrícia Souza", "patricia.souza@essor.com.br", "11987652221", "ESSOR"),
    ("Fernando Alves", "fernando.alves@essor.com.br", "11987652222", "ESSOR"),
    ("Luciana Martins", "luciana.martins@essor.com.br", "11987652223", "ESSOR"),
    
    # DAYCOVAL
    ("Ricardo Pereira", "ricardo.pereira@daycoval.com.br", "11987653331", "DAYCOVAL"),
    ("Camila Rodrigues", "camila.rodrigues@daycoval.com.br", "11987653332", "DAYCOVAL"),
    ("Bruno Nascimento", "bruno.nascimento@daycoval.com.br", "11987653333", "DAYCOVAL")
]

RESPONSAVEIS = [
    "Pedro Carvalho", "Maria Silva", "João Santos", "Ana Costa",
    "Equipe Técnica", "Suporte Nível 1", "Suporte Nível 2"
]

async def criar_usuarios():
    """Cria todos os usuários (admins e clientes)"""
    print("\n👥 CRIANDO USUÁRIOS...")
    print("="*80)
    
    # Limpar usuários existentes
    await db.users.delete_many({})
    
    usuarios_criados = []
    senha_padrao = "S@muka91"  # Para admins
    senha_cliente = "senha123"  # Para clientes
    
    # Criar administradores
    print("\n  👨‍💼 Administradores:")
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
        print(f"    ✅ {nome} - {email}")
    
    # Criar clientes
    print("\n  👤 Clientes:")
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
        print(f"    ✅ {nome} - {email} ({seguradora})")
    
    return usuarios_criados

async def criar_casos(usuarios_ids):
    """Cria 75 casos distribuídos pelas seguradoras"""
    print("\n📊 CRIANDO CASOS...")
    print("="*80)
    
    # Limpar casos existentes
    await db.cases.delete_many({})
    
    casos_criados = []
    caso_numero = 1
    
    # Data base (7 dias atrás)
    data_base = datetime.utcnow() - timedelta(days=7)
    
    for seguradora in SEGURADORAS:
        print(f"\n  📌 {seguradora}:")
        
        # 25 casos por seguradora
        for i in range(25):
            case_id = str(uuid.uuid4())
            
            # Definir status (60% concluídos, 40% em andamento)
            if i < 15:
                status = "Concluído"
            else:
                status = random.choice(["Pendente", "Em Desenvolvimento", "Aguardando resposta"])
            
            # Data aleatória nos últimos 7 dias
            dias_atras = random.randint(0, 7)
            data_criacao = data_base + timedelta(days=dias_atras, hours=random.randint(0, 23))
            
            # Escolher criador aleatório (cliente ou admin)
            creator_id = random.choice(usuarios_ids)
            
            caso = {
                "id": case_id,
                "jira_id": f"SGSS-N{caso_numero:03d}",
                "title": f"Caso {caso_numero} - {random.choice(['Suporte técnico', 'Dúvida sistema', 'Erro integração', 'Atualização cadastro', 'Consulta relatório'])}",
                "description": f"Descrição detalhada do caso {caso_numero} para a seguradora {seguradora}.",
                "status": status,
                "priority": random.choice(PRIORIDADES),
                "category": random.choice(CATEGORIAS),
                "seguradora": seguradora,
                "responsible": random.choice(RESPONSAVEIS),
                "creator_id": creator_id,
                "created_at": data_criacao.isoformat() + "Z",
                "updated_at": (data_criacao + timedelta(hours=random.randint(1, 48))).isoformat() + "Z"
            }
            
            if status == "Concluído":
                caso["completed_at"] = (data_criacao + timedelta(days=random.randint(1, 3))).isoformat() + "Z"
            
            await db.cases.insert_one(caso)
            casos_criados.append(case_id)
            caso_numero += 1
        
        print(f"    ✅ 25 casos criados ({seguradora})")
    
    return casos_criados

async def criar_comentarios(casos_ids, usuarios_ids):
    """Cria comentários nos casos"""
    print("\n💬 CRIANDO COMENTÁRIOS...")
    print("="*80)
    
    # Limpar comentários existentes
    await db.comments.delete_many({})
    
    comentarios_exemplos = [
        "Estou analisando o caso.",
        "Preciso de mais informações sobre o problema.",
        "O caso foi resolvido com sucesso.",
        "Encaminhado para o time técnico.",
        "Aguardando retorno do cliente.",
        "Solução aplicada e testada.",
        "Caso em desenvolvimento.",
        "Prioridade aumentada devido à urgência.",
        "Cliente confirmou resolução.",
        "Necessário acesso ao sistema para verificar."
    ]
    
    total_comentarios = 0
    
    # Adicionar 1-3 comentários em 50% dos casos
    casos_com_comentarios = random.sample(casos_ids, k=len(casos_ids)//2)
    
    for case_id in casos_com_comentarios:
        num_comentarios = random.randint(1, 3)
        
        for i in range(num_comentarios):
            comment_id = str(uuid.uuid4())
            is_internal = random.choice([True, False])
            
            comentario = {
                "id": comment_id,
                "case_id": case_id,
                "user_id": random.choice(usuarios_ids),
                "content": random.choice(comentarios_exemplos),
                "is_internal": is_internal,
                "created_at": (datetime.utcnow() - timedelta(hours=random.randint(1, 72))).isoformat() + "Z"
            }
            
            await db.comments.insert_one(comentario)
            total_comentarios += 1
    
    print(f"    ✅ {total_comentarios} comentários criados")
    return total_comentarios

async def criar_notificacoes(usuarios_ids):
    """Cria notificações para os usuários"""
    print("\n🔔 CRIANDO NOTIFICAÇÕES...")
    print("="*80)
    
    # Limpar notificações existentes
    await db.notifications.delete_many({})
    
    mensagens_notificacao = [
        ("Novo caso atribuído a você", "case_assigned"),
        ("Comentário adicionado ao seu caso", "comment_added"),
        ("Status do caso atualizado", "case_updated"),
        ("Caso marcado como concluído", "case_completed"),
        ("Novo comentário interno", "internal_comment"),
        ("Prioridade do caso alterada", "priority_changed")
    ]
    
    total_notificacoes = 0
    
    # Criar 2-5 notificações para cada usuário
    for user_id in usuarios_ids:
        num_notificacoes = random.randint(2, 5)
        
        for i in range(num_notificacoes):
            notif_id = str(uuid.uuid4())
            mensagem, tipo = random.choice(mensagens_notificacao)
            
            # 70% não lidas, 30% lidas
            is_read = random.random() < 0.3
            
            notificacao = {
                "id": notif_id,
                "user_id": user_id,
                "message": mensagem,
                "type": tipo,
                "is_read": is_read,
                "created_at": (datetime.utcnow() - timedelta(hours=random.randint(1, 168))).isoformat() + "Z"
            }
            
            if is_read:
                notificacao["read_at"] = (datetime.utcnow() - timedelta(hours=random.randint(0, 24))).isoformat() + "Z"
            
            await db.notifications.insert_one(notificacao)
            total_notificacoes += 1
    
    print(f"    ✅ {total_notificacoes} notificações criadas")
    return total_notificacoes

async def criar_atividades(casos_ids, usuarios_ids):
    """Cria registro de atividades"""
    print("\n📝 CRIANDO ATIVIDADES...")
    print("="*80)
    
    # Limpar atividades existentes
    await db.activities.delete_many({})
    
    tipos_atividade = [
        "case_created",
        "case_updated",
        "case_completed",
        "comment_added",
        "status_changed",
        "priority_changed"
    ]
    
    total_atividades = 0
    
    # Criar 1-2 atividades para cada caso
    for case_id in casos_ids:
        num_atividades = random.randint(1, 2)
        
        for i in range(num_atividades):
            activity_id = str(uuid.uuid4())
            
            atividade = {
                "id": activity_id,
                "case_id": case_id,
                "user_id": random.choice(usuarios_ids),
                "action": random.choice(tipos_atividade),
                "details": "Atividade registrada automaticamente",
                "created_at": (datetime.utcnow() - timedelta(hours=random.randint(1, 168))).isoformat() + "Z"
            }
            
            await db.activities.insert_one(atividade)
            total_atividades += 1
    
    print(f"    ✅ {total_atividades} atividades criadas")
    return total_atividades

async def mostrar_resumo():
    """Mostra resumo dos dados no banco"""
    print("\n" + "="*80)
    print("📊 RESUMO COMPLETO DO SISTEMA SAFE2GO")
    print("="*80)
    
    # Contar documentos
    total_users = await db.users.count_documents({})
    total_admins = await db.users.count_documents({"role": "administrador"})
    total_clients = await db.users.count_documents({"role": "cliente"})
    
    total_cases = await db.cases.count_documents({})
    completed = await db.cases.count_documents({"status": "Concluído"})
    pending = await db.cases.count_documents({"status": "Pendente"})
    in_dev = await db.cases.count_documents({"status": "Em Desenvolvimento"})
    waiting = await db.cases.count_documents({"status": "Aguardando resposta"})
    
    total_comments = await db.comments.count_documents({})
    internal_comments = await db.comments.count_documents({"is_internal": True})
    public_comments = await db.comments.count_documents({"is_internal": False})
    
    total_notifications = await db.notifications.count_documents({})
    unread_notif = await db.notifications.count_documents({"is_read": False})
    
    total_activities = await db.activities.count_documents({})
    
    # Casos por seguradora
    avla_cases = await db.cases.count_documents({"seguradora": "AVLA"})
    essor_cases = await db.cases.count_documents({"seguradora": "ESSOR"})
    daycoval_cases = await db.cases.count_documents({"seguradora": "DAYCOVAL"})
    
    print(f"\n  👥 USUÁRIOS: {total_users}")
    print(f"    • Administradores: {total_admins}")
    print(f"    • Clientes: {total_clients}")
    
    print(f"\n  📊 CASOS: {total_cases}")
    print(f"    • Concluídos: {completed} ({completed/total_cases*100:.1f}%)")
    print(f"    • Pendentes: {pending}")
    print(f"    • Em Desenvolvimento: {in_dev}")
    print(f"    • Aguardando resposta: {waiting}")
    
    print(f"\n  🏢 CASOS POR SEGURADORA:")
    print(f"    • AVLA: {avla_cases}")
    print(f"    • ESSOR: {essor_cases}")
    print(f"    • DAYCOVAL: {daycoval_cases}")
    
    print(f"\n  💬 COMENTÁRIOS: {total_comments}")
    print(f"    • Públicos: {public_comments}")
    print(f"    • Internos: {internal_comments}")
    
    print(f"\n  🔔 NOTIFICAÇÕES: {total_notifications}")
    print(f"    • Não lidas: {unread_notif}")
    print(f"    • Lidas: {total_notifications - unread_notif}")
    
    print(f"\n  📝 ATIVIDADES: {total_activities}")
    
    print("\n" + "="*80)
    print("✅ POPULAÇÃO COMPLETA DE DADOS FINALIZADA COM SUCESSO!")
    print("="*80)
    
    print("\n📋 CREDENCIAIS DE ACESSO:")
    print("\n  👨‍💼 ADMINISTRADORES (senha: S@muka91):")
    for nome, email, _ in NOMES_ADMINS:
        print(f"    • {email}")
    
    print("\n  👤 CLIENTES (senha: senha123):")
    for nome, email, _, seguradora in NOMES_CLIENTES:
        print(f"    • {email} ({seguradora})")
    
    print("\n" + "="*80)

async def main():
    print("\n" + "="*80)
    print("🚀 POPULAÇÃO COMPLETA DO SISTEMA SAFE2GO HELPDESK")
    print("="*80)
    
    # Criar usuários
    usuarios_ids = await criar_usuarios()
    
    # Criar casos
    casos_ids = await criar_casos(usuarios_ids)
    
    # Criar comentários
    await criar_comentarios(casos_ids, usuarios_ids)
    
    # Criar notificações
    await criar_notificacoes(usuarios_ids)
    
    # Criar atividades
    await criar_atividades(casos_ids, usuarios_ids)
    
    # Mostrar resumo
    await mostrar_resumo()

if __name__ == "__main__":
    asyncio.run(main())
