from fastapi import FastAPI, APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Set
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import json
import asyncio
import httpx  # Para sincronização com Jira
import base64  # Para autenticação no Jira

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 168  # 7 dias

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket conectado. Total de conexões: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket desconectado. Total de conexões: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Envia mensagem para todos os clientes conectados"""
        logger.info(f"📡 Broadcasting mensagem para {len(self.active_connections)} conexões: {message.get('type')}")
        
        if len(self.active_connections) == 0:
            logger.warning("⚠️ Nenhuma conexão WebSocket ativa para broadcast")
            return
        
        disconnected = set()
        success_count = 0
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                success_count += 1
                logger.info(f"✅ Mensagem enviada com sucesso para 1 conexão")
            except Exception as e:
                logger.error(f"❌ Erro ao enviar mensagem WebSocket: {e}")
                disconnected.add(connection)
        
        # Remover conexões com erro
        for conn in disconnected:
            self.active_connections.discard(conn)
        
        logger.info(f"📊 Broadcast concluído: {success_count} sucessos, {len(disconnected)} falhas")

manager = ConnectionManager()

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    role: str = "cliente"  # "cliente" ou "administrador"
    status: str = "pendente"  # "pendente", "aprovado", "rejeitado"
    phone: Optional[str] = None
    company: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None
    company: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    token: str
    user: User

class UserApproval(BaseModel):
    status: str  # "aprovado" ou "rejeitado"
    
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
class Comment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str
    user_id: str
    user_name: str
    content: str
    is_internal: bool = False  # True = observação interna (só ADM), False = resposta ao cliente
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CommentCreate(BaseModel):
    content: str
    is_internal: bool = False

class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    case_id: str
    case_title: str
    message: str
    type: str  # "new_comment", "status_change", "case_assigned"
    read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Case(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    jira_id: str
    title: str
    description: str
    responsible: str
    creator_id: Optional[str] = None  # ID do usuário que criou o chamado
    creator_name: Optional[str] = None  # Nome do usuário que criou
    status: str  # Concluído, Pendente, "Aguardando resposta do cliente"
    priority: Optional[str] = "Média"  # Baixa, Média, Alta, Urgente
    seguradora: Optional[str] = None  # AVLA, DAYCOVAL, ESSOR
    category: Optional[str] = None  # Categoria do erro
    keywords: List[str] = []  # Palavras-chave
    opened_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    solution: Optional[str] = None  # Como o caso foi resolvido
    solution_title: Optional[str] = None  # Título da solução para busca
    solved_by: Optional[str] = None  # Nome de quem resolveu
    solved_by_id: Optional[str] = None  # ID de quem resolveu
    solved_at: Optional[datetime] = None  # Data da resolução

class CaseCreate(BaseModel):
    jira_id: Optional[str] = None
    title: str
    description: str
    priority: str = "Média"
    responsible: str = "Não atribuído"
    status: str = "Pendente"
    seguradora: Optional[str] = None
    category: Optional[str] = None
    keywords: List[str] = []
    opened_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None

class CaseUpdate(BaseModel):
    jira_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    responsible: Optional[str] = None
    status: Optional[str] = None
    seguradora: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[List[str]] = None
    opened_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    solution: Optional[str] = None  # Notas de resolução
    solution_title: Optional[str] = None  # Título da solução
    solved_by: Optional[str] = None  # Nome de quem resolveu
    solved_by_id: Optional[str] = None  # ID de quem resolveu
    solved_at: Optional[datetime] = None  # Data da resolução

class Activity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: Optional[str] = None
    responsible: str
    activity: str
    time_spent: int  # minutes
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_current: bool = False  # indica se é a atividade atual

class ActivityCreate(BaseModel):
    case_id: Optional[str] = None
    responsible: str
    activity: str
    time_spent: int = 0
    notes: Optional[str] = None
    is_current: bool = False

class DashboardStats(BaseModel):
    total_cases: int
    completed_cases: int
    pending_cases: int
    in_development_cases: int
    waiting_client_cases: int
    waiting_config_cases: int
    completion_percentage: float
    cases_by_seguradora: dict = {}

class ChartData(BaseModel):
    date: str
    completed: int
    pending: int
    in_development: int = 0
    waiting: int = 0
    waiting_config: int = 0

class RecurrentCaseAnalysis(BaseModel):
    category: str
    count: int
    cases: List[dict] = []
    percentage: float
    suggestion: str

class CategoryStats(BaseModel):
    category: str
    count: int
    status_breakdown: dict = {}

class SimilarCase(BaseModel):
    case: Case
    similarity_score: float
    matching_keywords: List[str]

class JiraWebhookPayload(BaseModel):
    webhookEvent: str
    issue: dict

# Auth Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('user_id')
        
        user = await db.users.find_one({'id': user_id}, {'_id': 0, 'password': 0})
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Routes
@api_router.get("/")
async def root():
    return {"message": "Suporte Safe2Go - Sistema de Gerenciamento"}

# WebSocket Route
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Manter conexão aberta e receber mensagens (se necessário)
            data = await websocket.receive_text()
            # Pode processar mensagens do cliente aqui se necessário
            logger.info(f"Mensagem recebida do WebSocket: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Erro no WebSocket: {e}")
        manager.disconnect(websocket)

# Auth Routes
@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({'email': user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Create user with status "pendente"
    user = User(
        name=user_data.name, 
        email=user_data.email,
        phone=user_data.phone,
        company=user_data.company,
        role="cliente",
        status="pendente"
    )
    user_doc = user.model_dump()
    user_doc['password'] = hash_password(user_data.password)
    user_doc['created_at'] = user_doc['created_at'].isoformat()
    
    await db.users.insert_one(user_doc)
    
    logger.info(f"Novo cadastro pendente: {user_data.email}")
    
    # Retornar mensagem de sucesso sem gerar token
    return {
        "message": "Cadastro realizado com sucesso! Aguarde a aprovação do administrador.",
        "status": "pendente",
        "email": user_data.email
    }

@api_router.post("/auth/login", response_model=AuthResponse)
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({'email': credentials.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    if not verify_password(credentials.password, user_doc['password']):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    # Verificar se usuário está aprovado
    if user_doc.get('status') == 'pendente':
        raise HTTPException(
            status_code=403, 
            detail="Seu cadastro ainda não foi aprovado. Aguarde a aprovação do administrador."
        )
    
    if user_doc.get('status') == 'rejeitado':
        raise HTTPException(
            status_code=403, 
            detail="Seu cadastro foi rejeitado. Entre em contato com o administrador."
        )
    
    # Convert to User model (exclude password)
    user_doc.pop('password', None)
    user_doc.pop('_id', None)
    if isinstance(user_doc['created_at'], str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    user = User(**user_doc)
    token = create_token(user.id)
    
    return AuthResponse(token=token, user=user)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    return User(**current_user)

# User Management (Admin only)
@api_router.get("/users", response_model=List[User])
async def list_users(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    # Verificar se é administrador
    if current_user.get('role') != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    
    # Filtrar por status se fornecido
    query = {}
    if status:
        query['status'] = status
    
    users = await db.users.find(query, {'_id': 0, 'password': 0}).to_list(1000)
    
    # Converter datas
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        if user.get('approved_at') and isinstance(user['approved_at'], str):
            user['approved_at'] = datetime.fromisoformat(user['approved_at'])
    
    return [User(**user) for user in users]

@api_router.get("/users/pending", response_model=List[User])
async def list_pending_users(current_user: dict = Depends(get_current_user)):
    """Lista apenas usuários pendentes de aprovação"""
    if current_user.get('role') != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    
    users = await db.users.find(
        {'status': 'pendente'}, 
        {'_id': 0, 'password': 0}
    ).to_list(1000)
    
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    return [User(**user) for user in users]

@api_router.post("/users/{user_id}/approve")
async def approve_user(
    user_id: str, 
    approval: UserApproval,
    current_user: dict = Depends(get_current_user)
):
    """Aprovar ou rejeitar cadastro de usuário"""
    if current_user.get('role') != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    
    if approval.status not in ['aprovado', 'rejeitado']:
        raise HTTPException(status_code=400, detail="Status inválido")
    
    user = await db.users.find_one({'id': user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Atualizar status
    update_data = {
        'status': approval.status,
        'approved_at': datetime.now(timezone.utc).isoformat(),
        'approved_by': current_user['id']
    }
    
    await db.users.update_one({'id': user_id}, {'$set': update_data})
    
    logger.info(f"Usuário {user['email']} {approval.status} por {current_user['email']}")
    
    return {
        "message": f"Usuário {approval.status} com sucesso",
        "user_id": user_id,
        "status": approval.status
    }

@api_router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Atualizar dados do usuário"""
    if current_user.get('role') != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    
    user = await db.users.find_one({'id': user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Preparar dados para atualização (apenas campos não None)
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    
    if update_data:
        await db.users.update_one({'id': user_id}, {'$set': update_data})
    
    # Buscar usuário atualizado
    updated_user = await db.users.find_one({'id': user_id}, {'_id': 0, 'password': 0})
    
    if isinstance(updated_user.get('created_at'), str):
        updated_user['created_at'] = datetime.fromisoformat(updated_user['created_at'])
    if updated_user.get('approved_at') and isinstance(updated_user['approved_at'], str):
        updated_user['approved_at'] = datetime.fromisoformat(updated_user['approved_at'])
    
    return User(**updated_user)

@api_router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Atualizar dados de um usuário (Admin only)"""
    if current_user.get('role') != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    
    # Buscar usuário existente
    existing_user = await db.users.find_one({'id': user_id}, {'_id': 0})
    if not existing_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Preparar dados para atualização
    update_dict = {k: v for k, v in user_update.model_dump().items() if v is not None}
    
    # Se email está sendo atualizado, verificar se já existe
    if 'email' in update_dict and update_dict['email'] != existing_user['email']:
        email_exists = await db.users.find_one({'email': update_dict['email']})
        if email_exists:
            raise HTTPException(status_code=400, detail="Este email já está em uso")
    
    # Validar role
    if 'role' in update_dict and update_dict['role'] not in ['cliente', 'administrador']:
        raise HTTPException(status_code=400, detail="Role inválido. Use 'cliente' ou 'administrador'")
    
    # Validar status
    if 'status' in update_dict and update_dict['status'] not in ['pendente', 'aprovado', 'rejeitado']:
        raise HTTPException(status_code=400, detail="Status inválido")
    
    if update_dict:
        await db.users.update_one({'id': user_id}, {'$set': update_dict})
    
    # Buscar usuário atualizado
    updated_user = await db.users.find_one({'id': user_id}, {'_id': 0})
    
    logger.info(f"Usuário {updated_user['email']} atualizado por {current_user['email']}")
    
    return User(**updated_user)

@api_router.post("/users/create", response_model=User)
async def create_user_direct(
    user_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Criar usuário diretamente (admin-only)"""
    if current_user.get('role') != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    
    # Verificar se email já existe
    existing_user = await db.users.find_one({'email': user_data['email']})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Hash da senha
    hashed_password = hash_password(user_data['password'])
    
    # Criar novo usuário
    new_user = {
        'id': str(uuid.uuid4()),
        'name': user_data['name'],
        'email': user_data['email'],
        'password': hashed_password,
        'phone': user_data.get('phone', ''),
        'company': user_data.get('company', ''),
        'role': user_data.get('role', 'cliente'),
        'status': user_data.get('status', 'aprovado'),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'approved_at': datetime.now(timezone.utc).isoformat(),
        'approved_by': current_user['id']
    }
    
    await db.users.insert_one(new_user)
    
    logger.info(f"Usuário {new_user['email']} criado por {current_user['email']}")
    
    # Retornar sem a senha
    new_user_response = {k: v for k, v in new_user.items() if k != 'password'}
    new_user_response['created_at'] = datetime.fromisoformat(new_user_response['created_at'])
    new_user_response['approved_at'] = datetime.fromisoformat(new_user_response['approved_at'])
    
    return User(**new_user_response)

@api_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Deletar usuário"""
    if current_user.get('role') != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    
    # Não permitir deletar a si mesmo
    if user_id == current_user['id']:
        raise HTTPException(status_code=400, detail="Você não pode deletar sua própria conta")
    
    result = await db.users.delete_one({'id': user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {"message": "Usuário deletado com sucesso", "user_id": user_id}

# Comments Routes
@api_router.post("/cases/{case_id}/comments", response_model=Comment)
async def create_comment(
    case_id: str,
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Adicionar comentário a um chamado"""
    # Verificar se caso existe
    case = await db.cases.find_one({'id': case_id})
    if not case:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    # Criar comentário
    comment = Comment(
        case_id=case_id,
        user_id=current_user['id'],
        user_name=current_user['name'],
        content=comment_data.content,
        is_internal=comment_data.is_internal
    )
    
    comment_doc = comment.model_dump()
    comment_doc['created_at'] = comment_doc['created_at'].isoformat()
    
    await db.comments.insert_one(comment_doc)
    
    # Atualizar timestamp do caso
    await db.cases.update_one(
        {'id': case_id},
        {'$set': {'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    # Criar notificação
    # Se cliente comentou, notificar admin
    # Se admin comentou e não é interno, notificar cliente (criador do caso)
    if not comment_data.is_internal:
        if current_user['role'] == 'cliente':
            # Cliente comentou, notificar admin
            admins = await db.users.find({'role': 'administrador'}, {'_id': 0, 'id': 1}).to_list(100)
            for admin in admins:
                notification = Notification(
                    user_id=admin['id'],
                    case_id=case_id,
                    case_title=case['title'],
                    message=f"O chamado #{case.get('jira_id', case_id[:8])} recebeu uma nova resposta do cliente.",
                    type="new_comment"
                )
                notif_doc = notification.model_dump()
                notif_doc['created_at'] = notif_doc['created_at'].isoformat()
                await db.notifications.insert_one(notif_doc)
        else:
            # Admin respondeu, notificar criador do caso
            if case.get('creator_id'):
                notification = Notification(
                    user_id=case['creator_id'],
                    case_id=case_id,
                    case_title=case['title'],
                    message=f"Seu chamado #{case.get('jira_id', case_id[:8])} recebeu uma nova resposta do suporte.",
                    type="new_comment"
                )
                notif_doc = notification.model_dump()
                notif_doc['created_at'] = notif_doc['created_at'].isoformat()
                await db.notifications.insert_one(notif_doc)
                
                # Broadcast via WebSocket
                await manager.broadcast({
                    "type": "new_notification",
                    "user_id": case['creator_id'],
                    "case_id": case_id,
                    "message": notification.message
                })
    
    logger.info(f"Comentário adicionado no caso {case_id} por {current_user['name']}")
    
    # Sincronizar com Jira se o caso tiver jira_id e não for comentário interno
    if not comment_data.is_internal and case.get('jira_id'):
        # Enviar comentário ao Jira em background (não bloquear resposta)
        asyncio.create_task(
            send_comment_to_jira(
                case['jira_id'],
                comment_data.content,
                current_user['name']
            )
        )
    
    return comment

@api_router.get("/cases/{case_id}/comments", response_model=List[Comment])
async def get_comments(
    case_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Listar comentários de um chamado"""
    # Se é cliente, não mostrar comentários internos
    query = {'case_id': case_id}
    if current_user['role'] == 'cliente':
        query['is_internal'] = False
    
    # Buscar comentários sem ordenação inicial
    comments = await db.comments.find(query, {'_id': 0}).to_list(1000)
    
    # Converter todas as datas para datetime UTC e ordenar em Python
    for comment in comments:
        if isinstance(comment.get('created_at'), str):
            dt = datetime.fromisoformat(comment['created_at'])
            # Converter para UTC para comparação correta
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc)
            comment['created_at'] = dt
    
    # Ordenar por data UTC (mais recentes primeiro)
    comments.sort(key=lambda x: x.get('created_at', datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    
    return [Comment(**comment) for comment in comments]

# Notifications Routes
@api_router.get("/notifications", response_model=List[Notification])
async def get_notifications(
    unread_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Listar notificações do usuário"""
    query = {'user_id': current_user['id']}
    if unread_only:
        query['read'] = False
    
    notifications = await db.notifications.find(query, {'_id': 0}).sort('created_at', -1).limit(50).to_list(50)
    
    for notif in notifications:
        if isinstance(notif.get('created_at'), str):
            notif['created_at'] = datetime.fromisoformat(notif['created_at'])
    
    return [Notification(**notif) for notif in notifications]

@api_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Marcar notificação como lida"""
    result = await db.notifications.update_one(
        {'id': notification_id, 'user_id': current_user['id']},
        {'$set': {'read': True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    
    return {"message": "Notificação marcada como lida"}

@api_router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(current_user: dict = Depends(get_current_user)):
    """Marcar todas as notificações como lidas"""
    await db.notifications.update_many(
        {'user_id': current_user['id'], 'read': False},
        {'$set': {'read': True}}
    )
    
    return {"message": "Todas as notificações marcadas como lidas"}

# Knowledge Base - Resolution Notes Routes
@api_router.get("/knowledge-base")
async def get_knowledge_base(
    search: Optional[str] = None,
    category: Optional[str] = None,
    seguradora: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Buscar notas de resolução (Base de Conhecimento)"""
    # Apenas casos concluídos com solução
    query = {
        'status': 'Concluído',
        'solution': {'$ne': None, '$exists': True}
    }
    
    # Filtrar por categoria
    if category and category != 'all':
        query['category'] = category
    
    # Filtrar por seguradora
    if seguradora and seguradora != 'all':
        query['seguradora'] = seguradora
    
    cases = await db.cases.find(query, {'_id': 0}).sort('solved_at', -1).to_list(500)
    
    # Filtrar por busca de texto
    if search:
        search_lower = search.lower()
        filtered_cases = []
        for case in cases:
            searchable_text = f"{case.get('title', '')} {case.get('description', '')} {case.get('solution', '')} {case.get('solution_title', '')} {case.get('category', '')} {case.get('jira_id', '')}".lower()
            if search_lower in searchable_text:
                filtered_cases.append(case)
        cases = filtered_cases
    
    # Formatar resposta
    result = []
    for case in cases:
        result.append({
            'id': case.get('id'),
            'jira_id': case.get('jira_id'),
            'title': case.get('title'),
            'description': case.get('description'),
            'category': case.get('category'),
            'seguradora': case.get('seguradora'),
            'solution': case.get('solution'),
            'solution_title': case.get('solution_title'),
            'solved_by': case.get('solved_by'),
            'solved_at': case.get('solved_at') or case.get('updated_at'),
            'keywords': case.get('keywords', [])
        })
    
    return result

@api_router.get("/knowledge-base/stats")
async def get_knowledge_base_stats(current_user: dict = Depends(get_current_user)):
    """Estatísticas da base de conhecimento"""
    # Total de notas de resolução
    total = await db.cases.count_documents({
        'status': 'Concluído',
        'solution': {'$ne': None, '$exists': True}
    })
    
    # Por categoria
    pipeline = [
        {'$match': {'status': 'Concluído', 'solution': {'$ne': None, '$exists': True}}},
        {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    by_category = await db.cases.aggregate(pipeline).to_list(100)
    
    # Por seguradora
    pipeline_seg = [
        {'$match': {'status': 'Concluído', 'solution': {'$ne': None, '$exists': True}}},
        {'$group': {'_id': '$seguradora', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    by_seguradora = await db.cases.aggregate(pipeline_seg).to_list(100)
    
    return {
        'total': total,
        'by_category': [{'category': item['_id'] or 'Outros', 'count': item['count']} for item in by_category],
        'by_seguradora': [{'seguradora': item['_id'] or 'Não especificada', 'count': item['count']} for item in by_seguradora]
    }

@api_router.get("/cases/{case_id}/similar")
async def get_similar_cases(
    case_id: str,
    limit: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """Buscar casos similares resolvidos para sugerir soluções"""
    import re
    
    # Buscar o caso atual
    current_case = await db.cases.find_one({'id': case_id}, {'_id': 0})
    if not current_case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    
    # Não mostrar sugestões para casos já concluídos
    if current_case.get('status') == 'Concluído':
        return []
    
    # Buscar casos concluídos com solução
    resolved_cases = await db.cases.find({
        'status': 'Concluído',
        'solution': {'$ne': None, '$exists': True},
        'id': {'$ne': case_id}  # Excluir o próprio caso
    }, {'_id': 0}).to_list(500)
    
    if not resolved_cases:
        return []
    
    # Extrair palavras-chave do caso atual
    current_title = current_case.get('title', '').lower()
    current_desc = current_case.get('description', '').lower()
    current_category = current_case.get('category', '')
    current_seguradora = current_case.get('seguradora', '')
    current_keywords = [kw.lower() for kw in current_case.get('keywords', [])]
    
    # Palavras a ignorar (stop words em português)
    stop_words = {'de', 'da', 'do', 'das', 'dos', 'em', 'no', 'na', 'nos', 'nas', 
                  'um', 'uma', 'uns', 'umas', 'o', 'a', 'os', 'as', 'e', 'é', 
                  'para', 'por', 'com', 'sem', 'que', 'se', 'não', 'mas', 'ou',
                  'ao', 'aos', 'à', 'às', 'pelo', 'pela', 'pelos', 'pelas'}
    
    # Extrair palavras significativas do título e descrição
    def extract_keywords(text):
        words = re.findall(r'\b\w{3,}\b', text.lower())
        return set(w for w in words if w not in stop_words)
    
    current_words = extract_keywords(f"{current_title} {current_desc}")
    
    # Calcular score de similaridade para cada caso resolvido
    scored_cases = []
    for case in resolved_cases:
        score = 0
        
        # Score por categoria igual (peso alto)
        if case.get('category') and case.get('category') == current_category:
            score += 30
        
        # Score por seguradora igual (peso médio)
        if case.get('seguradora') and case.get('seguradora') == current_seguradora:
            score += 20
        
        # Score por palavras em comum no título e descrição
        case_text = f"{case.get('title', '')} {case.get('description', '')} {case.get('solution', '')}"
        case_words = extract_keywords(case_text)
        common_words = current_words.intersection(case_words)
        score += len(common_words) * 5
        
        # Score por keywords em comum
        case_keywords = set(kw.lower() for kw in case.get('keywords', []))
        common_keywords = set(current_keywords).intersection(case_keywords)
        score += len(common_keywords) * 10
        
        # Só incluir se tiver score mínimo
        if score >= 10:
            scored_cases.append({
                'case': case,
                'score': score,
                'common_words': list(common_words)[:5]  # Mostrar até 5 palavras em comum
            })
    
    # Ordenar por score e pegar os top N
    scored_cases.sort(key=lambda x: x['score'], reverse=True)
    top_cases = scored_cases[:limit]
    
    # Formatar resposta
    result = []
    for item in top_cases:
        case = item['case']
        result.append({
            'id': case.get('id'),
            'jira_id': case.get('jira_id'),
            'title': case.get('title'),
            'category': case.get('category'),
            'seguradora': case.get('seguradora'),
            'solution_title': case.get('solution_title'),
            'solution': case.get('solution'),
            'solved_by': case.get('solved_by'),
            'solved_at': case.get('solved_at') or case.get('updated_at'),
            'similarity_score': item['score'],
            'matching_keywords': item['common_words']
        })
    
    return result

# Cases CRUD
@api_router.post("/cases", response_model=Case)
async def create_case(case: CaseCreate, current_user: dict = Depends(get_current_user)):
    # Gerar jira_id se não fornecido
    if not case.jira_id:
        # Gerar ID único no formato S2GSS-XXXXX
        count = await db.cases.count_documents({})
        case.jira_id = f"S2GSS-{count + 1:05d}"
    
    case_dict = case.model_dump()
    case_dict['creator_id'] = current_user['id']
    case_dict['creator_name'] = current_user['name']
    
    if case_dict.get('opened_date') is None:
        case_dict['opened_date'] = datetime.now(timezone.utc)
    
    case_obj = Case(**case_dict)
    doc = case_obj.model_dump()
    
    # Serialize datetime to ISO string
    doc['opened_date'] = doc['opened_date'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc['closed_date']:
        doc['closed_date'] = doc['closed_date'].isoformat()
    
    await db.cases.insert_one(doc)
    return case_obj

@api_router.get("/cases", response_model=List[Case])
async def get_cases(
    responsible: Optional[str] = None,
    status: Optional[str] = None,
    days: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    
    # Se é cliente, mostrar apenas seus chamados
    if current_user['role'] == 'cliente':
        query['creator_id'] = current_user['id']
    
    if responsible:
        query['responsible'] = responsible
    if status:
        query['status'] = status
    if days:
        date_limit = datetime.now(timezone.utc) - timedelta(days=days)
        query['created_at'] = {"$gte": date_limit.isoformat()}
    
    cases = await db.cases.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Convert ISO string timestamps back to datetime
    for case in cases:
        # Handle opened_date if exists (backwards compatibility)
        if case.get('opened_date') and isinstance(case['opened_date'], str):
            case['opened_date'] = datetime.fromisoformat(case['opened_date'])
        # Use created_at as opened_date if opened_date doesn't exist
        elif not case.get('opened_date') and case.get('created_at'):
            case['opened_date'] = datetime.fromisoformat(case['created_at']) if isinstance(case['created_at'], str) else case['created_at']
        
        if case.get('closed_date') and isinstance(case['closed_date'], str):
            case['closed_date'] = datetime.fromisoformat(case['closed_date'])
        if isinstance(case.get('created_at', ''), str):
            case['created_at'] = datetime.fromisoformat(case['created_at'])
    
    return cases

# Analytics - Casos Recorrentes (DEVE VIR ANTES DE /cases/{case_id})
@api_router.get("/cases/analytics/recurrent", response_model=List[RecurrentCaseAnalysis])
async def get_recurrent_cases():
    """Analisa casos recorrentes por categoria"""
    # Buscar todos os casos
    all_cases = await db.cases.find({}, {"_id": 0}).to_list(1000)
    
    # Agrupar por categoria
    category_groups = {}
    total_cases = len(all_cases)
    
    for case in all_cases:
        category = case.get('category') or 'Não categorizado'
        if category not in category_groups:
            category_groups[category] = []
        category_groups[category].append(case)
    
    # Criar análise
    analysis = []
    for category, cases in category_groups.items():
        count = len(cases)
        percentage = (count / total_cases * 100) if total_cases > 0 else 0
        
        # Sugestão de automação baseada na quantidade
        if count >= 5:
            suggestion = f"🔴 CRÍTICO: {count} casos recorrentes. Automação URGENTE recomendada!"
        elif count >= 3:
            suggestion = f"🟡 ATENÇÃO: {count} casos. Considerar automação."
        else:
            suggestion = f"🟢 {count} caso(s). Monitorar evolução."
        
        # Converter datetime fields
        for case in cases:
            # Handle opened_date if exists (backwards compatibility)
            if case.get('opened_date') and isinstance(case.get('opened_date'), str):
                case['opened_date'] = datetime.fromisoformat(case['opened_date'])
            # Use created_at as opened_date if opened_date doesn't exist
            elif not case.get('opened_date') and case.get('created_at'):
                case['opened_date'] = datetime.fromisoformat(case['created_at']) if isinstance(case['created_at'], str) else case['created_at']
            
            if case.get('closed_date') and isinstance(case['closed_date'], str):
                case['closed_date'] = datetime.fromisoformat(case['closed_date'])
            if isinstance(case.get('created_at'), str):
                case['created_at'] = datetime.fromisoformat(case['created_at'])
        
        analysis.append(RecurrentCaseAnalysis(
            category=category,
            count=count,
            cases=cases[:5],  # Mostrar apenas os 5 primeiros
            percentage=round(percentage, 1),
            suggestion=suggestion
        ))
    
    # Ordenar por quantidade (maior primeiro)
    analysis.sort(key=lambda x: x.count, reverse=True)
    
    return analysis

@api_router.get("/cases/categories", response_model=List[CategoryStats])
async def get_categories(current_user: dict = Depends(get_current_user)):
    """Lista todas as categorias com estatísticas"""
    # Construir filtro inicial - se cliente, apenas seus casos
    match_stage = {}
    if current_user['role'] == 'cliente':
        match_stage = {"$match": {"creator_id": current_user['id']}}
    
    pipeline = []
    if match_stage:
        pipeline.append(match_stage)
    
    pipeline.extend([
        {
            "$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "statuses": {"$push": "$status"}
            }
        },
        {"$sort": {"count": -1}}
    ])
    
    results = await db.cases.aggregate(pipeline).to_list(100)
    
    category_stats = []
    for result in results:
        category = result['_id'] if result['_id'] else 'Não categorizado'
        statuses = result['statuses']
        
        # Contar status
        status_breakdown = {}
        for status in statuses:
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        category_stats.append(CategoryStats(
            category=category,
            count=result['count'],
            status_breakdown=status_breakdown
        ))
    
    return category_stats

@api_router.get("/cases/similar/{case_id}", response_model=List[SimilarCase])
async def get_similar_cases(case_id: str, limit: int = 5):
    """Encontra casos similares baseado em keywords e categoria"""
    # Buscar o caso original
    case = await db.cases.find_one({"id": case_id}, {"_id": 0})
    if not case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    
    case_keywords = set(case.get('keywords', []))
    case_category = case.get('category')
    
    # Buscar casos similares
    all_cases = await db.cases.find({"id": {"$ne": case_id}}, {"_id": 0}).to_list(1000)
    
    similar_cases = []
    for other_case in all_cases:
        other_keywords = set(other_case.get('keywords', []))
        other_category = other_case.get('category')
        
        # Calcular score de similaridade
        matching_keywords = case_keywords.intersection(other_keywords)
        keyword_score = len(matching_keywords) / max(len(case_keywords), 1) if case_keywords else 0
        category_score = 0.5 if case_category == other_category else 0
        
        total_score = (keyword_score * 0.7) + (category_score * 0.3)
        
        if total_score > 0:
            # Convert datetime fields
            # Handle opened_date if exists (backwards compatibility)
            if other_case.get('opened_date') and isinstance(other_case.get('opened_date'), str):
                other_case['opened_date'] = datetime.fromisoformat(other_case['opened_date'])
            # Use created_at as opened_date if opened_date doesn't exist
            elif not other_case.get('opened_date') and other_case.get('created_at'):
                other_case['opened_date'] = datetime.fromisoformat(other_case['created_at']) if isinstance(other_case['created_at'], str) else other_case['created_at']
            
            if other_case.get('closed_date') and isinstance(other_case['closed_date'], str):
                other_case['closed_date'] = datetime.fromisoformat(other_case['closed_date'])
            if isinstance(other_case.get('created_at'), str):
                other_case['created_at'] = datetime.fromisoformat(other_case['created_at'])
            
            similar_cases.append(SimilarCase(
                case=Case(**other_case),
                similarity_score=round(total_score * 100, 1),
                matching_keywords=list(matching_keywords)
            ))
    
    # Ordenar por score
    similar_cases.sort(key=lambda x: x.similarity_score, reverse=True)
    
    return similar_cases[:limit]

@api_router.get("/cases/{case_id}", response_model=Case)
async def get_case(case_id: str):
    case = await db.cases.find_one({"id": case_id}, {"_id": 0})
    if not case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    
    # Handle opened_date if exists (backwards compatibility)
    if case.get('opened_date') and isinstance(case['opened_date'], str):
        case['opened_date'] = datetime.fromisoformat(case['opened_date'])
    # Use created_at as opened_date if opened_date doesn't exist
    elif not case.get('opened_date') and case.get('created_at'):
        case['opened_date'] = datetime.fromisoformat(case['created_at']) if isinstance(case['created_at'], str) else case['created_at']
    
    if case.get('closed_date') and isinstance(case['closed_date'], str):
        case['closed_date'] = datetime.fromisoformat(case['closed_date'])
    if isinstance(case.get('created_at', ''), str):
        case['created_at'] = datetime.fromisoformat(case['created_at'])
    
    return case

@api_router.put("/cases/{case_id}", response_model=Case)
async def update_case(case_id: str, case_update: CaseUpdate):
    existing_case = await db.cases.find_one({"id": case_id}, {"_id": 0})
    if not existing_case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    
    update_dict = {k: v for k, v in case_update.model_dump().items() if v is not None}
    
    # Serialize datetime fields
    if 'opened_date' in update_dict and update_dict['opened_date']:
        update_dict['opened_date'] = update_dict['opened_date'].isoformat()
    if 'closed_date' in update_dict and update_dict['closed_date']:
        update_dict['closed_date'] = update_dict['closed_date'].isoformat()
    
    if update_dict:
        await db.cases.update_one({"id": case_id}, {"$set": update_dict})
    
    updated_case = await db.cases.find_one({"id": case_id}, {"_id": 0})
    
    # Convert back to datetime
    # Handle opened_date if exists (backwards compatibility)
    if updated_case.get('opened_date') and isinstance(updated_case['opened_date'], str):
        updated_case['opened_date'] = datetime.fromisoformat(updated_case['opened_date'])
    # Use created_at as opened_date if opened_date doesn't exist
    elif not updated_case.get('opened_date') and updated_case.get('created_at'):
        updated_case['opened_date'] = datetime.fromisoformat(updated_case['created_at']) if isinstance(updated_case['created_at'], str) else updated_case['created_at']
    
    if updated_case.get('closed_date') and isinstance(updated_case['closed_date'], str):
        updated_case['closed_date'] = datetime.fromisoformat(updated_case['closed_date'])
    if isinstance(updated_case.get('created_at', ''), str):
        updated_case['created_at'] = datetime.fromisoformat(updated_case['created_at'])
    
    return Case(**updated_case)

@api_router.delete("/cases/{case_id}")
async def delete_case(case_id: str, current_user: dict = Depends(get_current_user)):
    # Apenas administradores podem deletar casos
    if current_user['role'] != 'administrador':
        raise HTTPException(status_code=403, detail="Apenas administradores podem deletar casos")
    
    result = await db.cases.delete_one({"id": case_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    
    # Notificar via WebSocket
    await manager.broadcast({
        "type": "case_deleted",
        "case_id": case_id
    })
    
    return {"message": "Caso deletado com sucesso"}

# Dashboard
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    seguradora: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    # Construir query base - se cliente, filtrar apenas seus casos
    base_query = {}
    if current_user['role'] == 'cliente':
        base_query['creator_id'] = current_user['id']
    
    # Adicionar filtro de seguradora se fornecido
    if seguradora:
        base_query['seguradora'] = seguradora
    
    # Adicionar filtro de data se fornecido
    if start_date or end_date:
        date_query = {}
        if start_date:
            # Adicionar hora 00:00:00 para incluir todo o dia inicial
            date_query['$gte'] = f"{start_date}T00:00:00"
        if end_date:
            # Adicionar hora 23:59:59 para incluir todo o dia final
            date_query['$lte'] = f"{end_date}T23:59:59"
        base_query['created_at'] = date_query
    
    total = await db.cases.count_documents(base_query)
    completed = await db.cases.count_documents({**base_query, "status": "Concluído"})
    pending = await db.cases.count_documents({**base_query, "status": "Pendente"})
    in_development = await db.cases.count_documents({**base_query, "status": "Em Desenvolvimento"})
    waiting_client = await db.cases.count_documents({**base_query, "status": {"$in": ["Aguardando resposta do cliente", "Aguardando resposta"]}})
    waiting_config = await db.cases.count_documents({**base_query, "status": "Aguardando Configuração"})
    
    percentage = (completed / total * 100) if total > 0 else 0
    
    # Contar casos por seguradora
    cases_by_seguradora = {}
    all_cases = await db.cases.find(base_query, {"_id": 0, "seguradora": 1}).to_list(1000)
    for case in all_cases:
        seguradora = case.get('seguradora', 'Não especificada')
        if not seguradora:
            seguradora = 'Não especificada'
        cases_by_seguradora[seguradora] = cases_by_seguradora.get(seguradora, 0) + 1
    
    return DashboardStats(
        total_cases=total,
        completed_cases=completed,
        pending_cases=pending,
        in_development_cases=in_development,
        waiting_client_cases=waiting_client,
        waiting_config_cases=waiting_config,
        completion_percentage=round(percentage, 1),
        cases_by_seguradora=cases_by_seguradora
    )

@api_router.get("/dashboard/charts", response_model=List[ChartData])
async def get_chart_data(
    seguradora: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    # Determinar período
    if start_date and end_date:
        # Usar período fornecido
        start = datetime.fromisoformat(start_date).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        end = datetime.fromisoformat(end_date).replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
        num_days = (end - start).days + 1
    else:
        # Usar últimos 7 dias como padrão
        num_days = 7
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=6)
    
    chart_data = []
    
    # Construir query base - se cliente, filtrar apenas seus casos
    base_query = {}
    if current_user['role'] == 'cliente':
        base_query['creator_id'] = current_user['id']
    
    # Adicionar filtro de seguradora se fornecido
    if seguradora:
        base_query['seguradora'] = seguradora
    
    # Adicionar filtro de status se fornecido (para gráficos específicos)
    status_filter = {}
    if status and status != 'all':
        status_filter = {'status': status}
    
    # Gerar dados para cada dia no período
    for i in range(num_days):
        if start_date and end_date:
            # Calcular data a partir do início
            date = start + timedelta(days=i)
        else:
            # Calcular data regressiva (últimos 7 dias)
            date = datetime.now(timezone.utc) - timedelta(days=num_days-1-i)
        
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        # Count completed and pending cases for this day
        day_query = {
            **base_query,
            **status_filter,
            "created_at": {
                "$gte": day_start.isoformat(),
                "$lt": day_end.isoformat()
            }
        }
        
        # Se filtro de status está ativo, contar apenas esse status
        if status and status != 'all':
            completed = await db.cases.count_documents({**day_query, "status": "Concluído"}) if status == 'Concluído' else 0
            pending = await db.cases.count_documents({**day_query, "status": "Pendente"}) if status == 'Pendente' else 0
            in_development = await db.cases.count_documents({**day_query, "status": "Em Desenvolvimento"}) if status == 'Em Desenvolvimento' else 0
            waiting = await db.cases.count_documents({**day_query, "status": "Aguardando resposta"}) if status == 'Aguardando resposta' else 0
            waiting_config = await db.cases.count_documents({**day_query, "status": "Aguardando Configuração"}) if status == 'Aguardando Configuração' else 0
        else:
            # Contar todos os status
            completed = await db.cases.count_documents({
                **day_query,
                "status": "Concluído"
            })
            
            pending = await db.cases.count_documents({
                **day_query,
                "status": "Pendente"
            })
            
            in_development = await db.cases.count_documents({
                **day_query,
                "status": "Em Desenvolvimento"
            })
            
            waiting = await db.cases.count_documents({
                **day_query,
                "status": "Aguardando resposta"
            })
            
            waiting_config = await db.cases.count_documents({
                **day_query,
                "status": "Aguardando Configuração"
            })
        
        chart_data.append(ChartData(
            date=day_start.strftime("%d/%m"),
            completed=completed,
            pending=pending,
            in_development=in_development,
            waiting=waiting,
            waiting_config=waiting_config
        ))
    
    return chart_data

@api_router.get("/dashboard/charts/detailed")
async def get_detailed_chart_data(
    seguradora: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    view_type: str = 'monthly',  # 'monthly' or 'weekly'
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para gráfico mensal/semanal detalhado com todos os status
    """
    # Construir query base
    base_query = {}
    if current_user['role'] == 'cliente':
        base_query['creator_id'] = current_user['id']
    
    if seguradora:
        base_query['seguradora'] = seguradora
    
    # Buscar o caso mais antigo e mais recente para determinar o período real
    oldest_case = await db.cases.find_one(base_query, sort=[('created_at', 1)])
    newest_case = await db.cases.find_one(base_query, sort=[('created_at', -1)])
    
    if not oldest_case or not newest_case:
        return []
    
    # Determinar período baseado nos dados reais
    if view_type == 'monthly':
        # Usar últimos 6 meses dos dados reais
        data_end = datetime.fromisoformat(newest_case['created_at'])
        data_start = data_end - timedelta(days=180)  # ~6 meses
        period_type = 'month'
    else:
        # Usar últimas 4 semanas dos dados reais
        if start_date and end_date:
            data_start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
            data_end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
        else:
            data_end = datetime.fromisoformat(newest_case['created_at'])
            data_start = data_end - timedelta(days=27)  # 4 semanas
        period_type = 'week'
    
    # Adicionar filtro de status se fornecido
    status_filter = {}
    if status and status != 'all':
        status_filter = {'status': status}
    
    chart_data = []
    
    if period_type == 'month':
        # Gerar lista de meses no período
        from dateutil.relativedelta import relativedelta
        import calendar
        
        current_month = data_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_month = data_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        while current_month <= end_month:
            # Calcular último dia do mês
            last_day = calendar.monthrange(current_month.year, current_month.month)[1]
            month_end = current_month.replace(day=last_day, hour=23, minute=59, second=59)
            
            # Query para o mês
            month_query = {
                **base_query,
                **status_filter,
                'created_at': {
                    '$gte': current_month.isoformat(),
                    '$lte': month_end.isoformat()
                }
            }
            
            # Contar por status
            if not status or status == 'all':
                completed = await db.cases.count_documents({**month_query, 'status': 'Concluído'})
                pending = await db.cases.count_documents({**month_query, 'status': 'Pendente'})
                in_development = await db.cases.count_documents({**month_query, 'status': 'Em Desenvolvimento'})
                waiting = await db.cases.count_documents({
                    **base_query,
                    'created_at': month_query['created_at'],
                    'status': {'$in': ['Aguardando resposta', 'Aguardando Configuração']}
                })
            else:
                # Se status específico, contar apenas esse
                count = await db.cases.count_documents(month_query)
                completed = count if status == 'Concluído' else 0
                pending = count if status == 'Pendente' else 0
                in_development = count if status == 'Em Desenvolvimento' else 0
                waiting = count if status in ['Aguardando resposta', 'Aguardando Configuração'] else 0
            
            chart_data.append({
                'date': current_month.strftime('%b/%y'),
                'completed': completed,
                'pending': pending,
                'in_development': in_development,
                'waiting': waiting
            })
            
            # Próximo mês
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)
    
    else:
        # Agrupar por semana (7 dias)
        num_days = (data_end - data_start).days + 1
        num_weeks = (num_days + 6) // 7  # Arredondar para cima
        
        for i in range(num_weeks):
            week_start = data_start + timedelta(days=i * 7)
            week_end = min(week_start + timedelta(days=6), data_end)
            
            week_query = {
                **base_query,
                **status_filter,
                'created_at': {
                    '$gte': week_start.isoformat(),
                    '$lte': week_end.isoformat()
                }
            }
            
            # Contar por status
            if not status or status == 'all':
                completed = await db.cases.count_documents({**week_query, 'status': 'Concluído'})
                pending = await db.cases.count_documents({**week_query, 'status': 'Pendente'})
                in_development = await db.cases.count_documents({**week_query, 'status': 'Em Desenvolvimento'})
                waiting = await db.cases.count_documents({
                    **base_query,
                    'created_at': week_query['created_at'],
                    'status': {'$in': ['Aguardando resposta', 'Aguardando Configuração']}
                })
            else:
                count = await db.cases.count_documents(week_query)
                completed = count if status == 'Concluído' else 0
                pending = count if status == 'Pendente' else 0
                in_development = count if status == 'Em Desenvolvimento' else 0
                waiting = count if status in ['Aguardando resposta', 'Aguardando Configuração'] else 0
            
            chart_data.append({
                'date': f"{week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')}",
                'completed': completed,
                'pending': pending,
                'in_development': in_development,
                'waiting': waiting
            })
    
    return chart_data

# Função auxiliar para enviar comentário ao Jira
async def send_comment_to_jira(jira_id: str, comment_text: str, author_name: str) -> bool:
    """
    Envia um comentário do Safe2Go para o Jira
    """
    try:
        jira_url = os.environ.get('JIRA_URL', '').strip()
        jira_email = os.environ.get('JIRA_EMAIL', '').strip()
        jira_api_token = os.environ.get('JIRA_API_TOKEN', '').strip()
        
        # Verificar se as credenciais estão configuradas
        if not jira_url or not jira_email or not jira_api_token:
            print("⚠️  Credenciais do Jira não configuradas. Comentário não será sincronizado.")
            return False
        
        # Criar autenticação básica
        auth_string = f"{jira_email}:{jira_api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_base64 = base64.b64encode(auth_bytes).decode('ascii')
        
        # Preparar o comentário com informação do autor
        comment_body = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": f"[Safe2Go - {author_name}] {comment_text}"
                            }
                        ]
                    }
                ]
            }
        }
        
        # URL da API do Jira
        api_url = f"{jira_url}/rest/api/3/issue/{jira_id}/comment"
        
        # Fazer requisição
        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_url,
                json=comment_body,
                headers={
                    "Authorization": f"Basic {auth_base64}",
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Comentário enviado ao Jira {jira_id}")
                return True
            else:
                print(f"❌ Erro ao enviar comentário ao Jira: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Erro ao enviar comentário ao Jira: {str(e)}")
        return False

# Função auxiliar para tratar comentários do Jira
async def handle_jira_comment(payload: dict):
    """
    Trata eventos de comentários vindos do Jira
    """
    try:
        webhook_event = payload.get('webhookEvent', '')
        comment = payload.get('comment', {})
        issue = payload.get('issue', {})
        
        if not comment or not issue:
            return {"status": "ignored", "reason": "Missing comment or issue data"}
        
        # Extrair dados
        issue_key = issue.get('key', '')
        comment_body = comment.get('body', '')
        comment_author = comment.get('author', {}).get('displayName', 'Jira User')
        comment_id = comment.get('id', '')
        created = comment.get('created', datetime.now(timezone.utc).isoformat())
        
        # Se body é um objeto (formato Jira moderno), extrair texto
        if isinstance(comment_body, dict):
            # Formato Atlassian Document Format (ADF)
            content_list = comment_body.get('content', [])
            text_parts = []
            for content_block in content_list:
                if content_block.get('type') == 'paragraph':
                    for text_node in content_block.get('content', []):
                        if text_node.get('type') == 'text':
                            text_parts.append(text_node.get('text', ''))
            comment_body = ' '.join(text_parts) if text_parts else 'Comentário sem texto'
        
        # Buscar o caso correspondente no Safe2Go
        case = await db.cases.find_one({'jira_id': issue_key})
        
        if not case:
            return {"status": "ignored", "reason": f"Case {issue_key} not found in Safe2Go"}
        
        # Verificar se o comentário já existe (evitar duplicatas)
        existing_comment = await db.comments.find_one({
            'case_id': case['id'],
            'jira_comment_id': comment_id
        })
        
        if existing_comment:
            return {"status": "ignored", "reason": "Comment already exists"}
        
        # Criar comentário no Safe2Go com campos corretos do modelo Comment
        comment_data = {
            'id': str(uuid.uuid4()),
            'case_id': case['id'],
            'user_id': case.get('creator_id') or 'jira-user',  # Garantir que nunca seja None
            'user_name': comment_author,
            'content': comment_body,
            'is_internal': False,  # Comentários do Jira são públicos
            'created_at': created,
            'jira_comment_id': comment_id,
            'synced_from_jira': True
        }
        
        await db.comments.insert_one(comment_data)
        
        # Criar notificação
        notification_data = {
            'id': str(uuid.uuid4()),
            'user_id': case.get('creator_id'),
            'case_id': case['id'],
            'message': f"Novo comentário no caso {issue_key} por {comment_author}",
            'type': 'comment',
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one(notification_data)
        
        return {
            "status": "comment_created",
            "case_id": issue_key,
            "comment_id": comment_id
        }
        
    except Exception as e:
        print(f"Error handling Jira comment: {str(e)}")
        return {"status": "error", "message": str(e)}

# Webhook do Jira
@api_router.post("/webhooks/jira")
async def jira_webhook(payload: dict):
    try:
        webhook_event = payload.get('webhookEvent', '')
        
        # Log para debug
        print(f"📥 Webhook recebido: {webhook_event}")
        print(f"📋 Payload keys: {list(payload.keys())}")
        
        # Tratar eventos de comentários
        if 'comment' in webhook_event:
            print("💬 Evento de comentário detectado")
            return await handle_jira_comment(payload)
        
        if 'issue' not in payload:
            print("⚠️  Payload sem 'issue', ignorando")
            return {"status": "ignored", "reason": "No issue data"}
        
        issue = payload['issue']
        issue_key = issue.get('key', '')
        fields = issue.get('fields', {})
        
        print(f"🔑 Issue key recebida: '{issue_key}'")
        
        # Extrair dados do Jira
        title = fields.get('summary', 'Sem título')
        description = fields.get('description', '')
        
        # Se description é um objeto (formato Jira moderno), extrair texto
        if isinstance(description, dict):
            description = description.get('content', [{}])[0].get('content', [{}])[0].get('text', 'Sem descrição')
        elif not description:
            description = 'Sem descrição'
        
        # Pegar assignee (responsável)
        assignee = fields.get('assignee', {})
        responsible = assignee.get('displayName', 'Equipe Suporte') if assignee else 'Equipe Suporte'
        
        # Mapear status do Jira para nosso sistema
        status_jira_raw = fields.get('status', {}).get('name', 'To Do')
        # Normalizar: remover pontos, espaços extras e converter para lowercase para comparação
        status_jira_normalized = status_jira_raw.strip().rstrip('.').lower()
        
        status_map = {
            'to do': 'Pendente',
            'in progress': 'Pendente',
            'em atendimento': 'Em Desenvolvimento',
            'done': 'Concluído',
            'closed': 'Concluído',
            'resolvido': 'Concluído',
            'resolved': 'Concluído',
            'concluído': 'Concluído',
            'concluido': 'Concluído',
            'aguardando cliente': 'Aguardando resposta',
            'waiting for customer': 'Aguardando resposta',
            'aguardando resposta': 'Aguardando resposta',
            'aguardando suporte': 'Pendente',
            'aguardando configuração': 'Aguardando Configuração',
            'aguardando configuracao': 'Aguardando Configuração',
            'pendentes s2g': 'Pendente',
            'pendente': 'Pendente',
        }
        status = status_map.get(status_jira_normalized, 'Pendente')
        
        print(f"📊 Status Jira: '{status_jira_raw}' (normalizado: '{status_jira_normalized}') -> Safe2Go: '{status}'")
        
        # Detectar seguradora do responsável ou descrição
        combined_text = f"{responsible} {title} {description}".upper()
        seguradora = None
        if 'AVLA' in combined_text:
            seguradora = 'AVLA'
        elif 'ESSOR' in combined_text:
            seguradora = 'ESSOR'
        elif 'DAYCOVAL' in combined_text:
            seguradora = 'DAYCOVAL'
        
        # Categorizar automaticamente
        combined_lower = f"{title} {description}".lower()
        category = None
        keywords = []
        
        if 'reprocessamento' in combined_lower or 'reprocessar' in combined_lower:
            category = 'Reprocessamento'
            keywords = ['reprocessamento', 'reprocessar']
        elif 'erro corretor' in combined_lower or 'corretor' in combined_lower:
            category = 'Erro Corretor'
            keywords = ['erro', 'corretor']
        elif 'nova lei' in combined_lower or 'adequação' in combined_lower or 'adequacao' in combined_lower:
            category = 'Adequação Nova Lei'
            keywords = ['nova lei', 'adequação']
        elif 'boleto' in combined_lower:
            category = 'Erro Boleto'
            keywords = ['boleto', 'pagamento']
        elif 'endosso' in combined_lower:
            category = 'Problema Endosso'
            keywords = ['endosso']
        elif 'sumiço' in combined_lower or 'sumico' in combined_lower:
            category = 'Sumiço de Dados'
            keywords = ['sumiço']
        elif 'integra' in combined_lower:
            category = 'Integração'
            keywords = ['integração', 'teste']
        else:
            category = 'Outros'
            keywords = []
        
        # Adicionar seguradora como keyword
        if seguradora:
            keywords.append(seguradora.lower())
        
        # Verificar se o caso já existe
        existing_case = await db.cases.find_one({'jira_id': issue_key})
        
        print(f"🔍 Verificando caso {issue_key}...")
        
        if existing_case:
            print(f"♻️  Caso existente encontrado, atualizando...")
            # Atualizar caso existente
            update_data = {
                'title': title,
                'description': description,
                'responsible': responsible,
                'status': status,
                'category': category,
                'keywords': keywords,
                'seguradora': seguradora
            }
            await db.cases.update_one({'jira_id': issue_key}, {'$set': update_data})
            logger.info(f"Caso atualizado via webhook: {issue_key}")
            
            # Notificar clientes WebSocket sobre atualização
            await manager.broadcast({
                "type": "case_updated",
                "case_id": issue_key,
                "title": title,
                "status": status
            })
            
            return {"status": "updated", "case_id": issue_key}
        else:
            print(f"✨ Criando novo caso {issue_key}...")
            print(f"   Título: {title}")
            print(f"   Status: {status}")
            print(f"   Seguradora: {seguradora}")
            print(f"   Categoria: {category}")
            
            # Criar novo caso
            new_case = Case(
                jira_id=issue_key,
                title=title,
                description=description,
                responsible=responsible,
                status=status,
                category=category,
                keywords=keywords,
                seguradora=seguradora
            )
            
            doc = new_case.model_dump()
            doc['opened_date'] = doc['opened_date'].isoformat()
            doc['created_at'] = doc['created_at'].isoformat()
            if doc['closed_date']:
                doc['closed_date'] = doc['closed_date'].isoformat()
            
            await db.cases.insert_one(doc)
            logger.info(f"Novo caso criado via webhook: {issue_key}")
            
            # Notificar TODOS os administradores sobre novo chamado via webhook
            admins = await db.users.find({'role': 'administrador', 'status': 'aprovado'}, {'_id': 0, 'id': 1}).to_list(100)
            for admin in admins:
                notification = Notification(
                    user_id=admin['id'],
                    case_id=new_case.id,
                    case_title=title,
                    message=f"🆕 Novo chamado via Jira: #{issue_key} - {title[:50]}{'...' if len(title) > 50 else ''}",
                    type="new_case"
                )
                notif_doc = notification.model_dump()
                notif_doc['created_at'] = notif_doc['created_at'].isoformat()
                await db.notifications.insert_one(notif_doc)
                logger.info(f"Notificação criada para admin {admin['id']}")
            
            # Notificar clientes WebSocket sobre novo caso
            await manager.broadcast({
                "type": "new_case",
                "case": {
                    "id": new_case.id,
                    "jira_id": issue_key,
                    "title": title,
                    "description": description,
                    "responsible": responsible,
                    "status": status,
                    "category": category,
                    "seguradora": seguradora,
                    "opened_date": doc['opened_date'],
                    "created_at": doc['created_at']
                }
            })
            
            # Broadcast notificação para admins via WebSocket
            await manager.broadcast({
                "type": "new_notification",
                "message": f"Novo chamado via Jira: #{issue_key}",
                "case_id": new_case.id,
                "jira_id": issue_key
            })
            
            return {"status": "created", "case_id": issue_key}
            
    except Exception as e:
        logger.error(f"Erro ao processar webhook do Jira: {str(e)}")
        return {"status": "error", "message": str(e)}

# Activities
@api_router.post("/activities", response_model=Activity)
async def create_activity(activity: ActivityCreate):
    # If this is a current activity, set all others for this responsible as not current
    if activity.is_current:
        await db.activities.update_many(
            {"responsible": activity.responsible, "is_current": True},
            {"$set": {"is_current": False}}
        )
    
    activity_obj = Activity(**activity.model_dump())
    doc = activity_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.activities.insert_one(doc)
    return activity_obj

@api_router.get("/activities", response_model=List[Activity])
async def get_activities(
    responsible: Optional[str] = None,
    case_id: Optional[str] = None,
    limit: int = 100
):
    query = {}
    if responsible:
        query['responsible'] = responsible
    if case_id:
        query['case_id'] = case_id
    
    activities = await db.activities.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    for activity in activities:
        if isinstance(activity['created_at'], str):
            activity['created_at'] = datetime.fromisoformat(activity['created_at'])
    
    return activities

@api_router.get("/activities/current", response_model=List[Activity])
async def get_current_activities():
    activities = await db.activities.find({"is_current": True}, {"_id": 0}).to_list(100)
    
    for activity in activities:
        if isinstance(activity['created_at'], str):
            activity['created_at'] = datetime.fromisoformat(activity['created_at'])
    
    return activities

@api_router.put("/activities/{activity_id}/stop")
async def stop_activity(activity_id: str):
    result = await db.activities.update_one(
        {"id": activity_id},
        {"$set": {"is_current": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Atividade não encontrada")
    return {"message": "Atividade parada"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()