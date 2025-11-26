from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt

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

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    token: str
    user: User
class Case(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    jira_id: str
    title: str
    description: str
    responsible: str
    status: str  # Concluído, Pendente
    seguradora: Optional[str] = None  # AVLA, DAYCOVAL, ESSOR
    category: Optional[str] = None  # Categoria do erro (ex: Reprocessamento, Erro Corretor, Nova Lei)
    keywords: List[str] = []  # Palavras-chave para busca de similaridade
    opened_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CaseCreate(BaseModel):
    jira_id: str
    title: str
    description: str
    responsible: str
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
    responsible: Optional[str] = None
    status: Optional[str] = None
    seguradora: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[List[str]] = None
    opened_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None

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
    waiting_client_cases: int
    completion_percentage: float
    cases_by_seguradora: dict = {}

class ChartData(BaseModel):
    date: str
    completed: int
    pending: int

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

# Auth Routes
@api_router.post("/auth/register", response_model=AuthResponse)
async def register(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({'email': user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Create user
    user = User(name=user_data.name, email=user_data.email)
    user_doc = user.model_dump()
    user_doc['password'] = hash_password(user_data.password)
    user_doc['created_at'] = user_doc['created_at'].isoformat()
    
    await db.users.insert_one(user_doc)
    
    # Generate token
    token = create_token(user.id)
    
    return AuthResponse(token=token, user=user)

@api_router.post("/auth/login", response_model=AuthResponse)
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({'email': credentials.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    if not verify_password(credentials.password, user_doc['password']):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
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

# Cases CRUD
@api_router.post("/cases", response_model=Case)
async def create_case(case: CaseCreate):
    case_dict = case.model_dump()
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
    days: Optional[int] = None
):
    query = {}
    
    if responsible:
        query['responsible'] = responsible
    if status:
        query['status'] = status
    if days:
        date_limit = datetime.now(timezone.utc) - timedelta(days=days)
        query['opened_date'] = {"$gte": date_limit.isoformat()}
    
    cases = await db.cases.find(query, {"_id": 0}).sort("opened_date", -1).to_list(1000)
    
    # Convert ISO string timestamps back to datetime
    for case in cases:
        if isinstance(case['opened_date'], str):
            case['opened_date'] = datetime.fromisoformat(case['opened_date'])
        if case.get('closed_date') and isinstance(case['closed_date'], str):
            case['closed_date'] = datetime.fromisoformat(case['closed_date'])
        if isinstance(case['created_at'], str):
            case['created_at'] = datetime.fromisoformat(case['created_at'])
    
    return cases

@api_router.get("/cases/{case_id}", response_model=Case)
async def get_case(case_id: str):
    case = await db.cases.find_one({"id": case_id}, {"_id": 0})
    if not case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    
    if isinstance(case['opened_date'], str):
        case['opened_date'] = datetime.fromisoformat(case['opened_date'])
    if case.get('closed_date') and isinstance(case['closed_date'], str):
        case['closed_date'] = datetime.fromisoformat(case['closed_date'])
    if isinstance(case['created_at'], str):
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
    if isinstance(updated_case['opened_date'], str):
        updated_case['opened_date'] = datetime.fromisoformat(updated_case['opened_date'])
    if updated_case.get('closed_date') and isinstance(updated_case['closed_date'], str):
        updated_case['closed_date'] = datetime.fromisoformat(updated_case['closed_date'])
    if isinstance(updated_case['created_at'], str):
        updated_case['created_at'] = datetime.fromisoformat(updated_case['created_at'])
    
    return Case(**updated_case)

@api_router.delete("/cases/{case_id}")
async def delete_case(case_id: str):
    result = await db.cases.delete_one({"id": case_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    return {"message": "Caso deletado com sucesso"}

# Dashboard
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    total = await db.cases.count_documents({})
    completed = await db.cases.count_documents({"status": "Concluído"})
    pending = await db.cases.count_documents({"status": "Pendente"})
    waiting_client = await db.cases.count_documents({"status": "Aguardando resposta do cliente"})
    
    percentage = (completed / total * 100) if total > 0 else 0
    
    # Contar casos por seguradora
    cases_by_seguradora = {}
    all_cases = await db.cases.find({}, {"_id": 0, "seguradora": 1}).to_list(1000)
    for case in all_cases:
        seguradora = case.get('seguradora', 'Não especificada')
        if not seguradora:
            seguradora = 'Não especificada'
        cases_by_seguradora[seguradora] = cases_by_seguradora.get(seguradora, 0) + 1
    
    return DashboardStats(
        total_cases=total,
        completed_cases=completed,
        pending_cases=pending,
        waiting_client_cases=waiting_client,
        completion_percentage=round(percentage, 1),
        cases_by_seguradora=cases_by_seguradora
    )

@api_router.get("/dashboard/charts", response_model=List[ChartData])
async def get_chart_data():
    # Get last 7 days data
    chart_data = []
    
    for i in range(6, -1, -1):
        date = datetime.now(timezone.utc) - timedelta(days=i)
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        # Count completed and pending cases for this day
        completed = await db.cases.count_documents({
            "opened_date": {
                "$gte": start_date.isoformat(),
                "$lt": end_date.isoformat()
            },
            "status": "Concluído"
        })
        
        pending = await db.cases.count_documents({
            "opened_date": {
                "$gte": start_date.isoformat(),
                "$lt": end_date.isoformat()
            },
            "status": "Pendente"
        })
        
        chart_data.append(ChartData(
            date=start_date.strftime("%d/%m"),
            completed=completed,
            pending=pending
        ))
    
    return chart_data

# Webhook do Jira
@api_router.post("/webhooks/jira")
async def jira_webhook(payload: dict):
    try:
        # Verificar se é um evento de criação de issue
        webhook_event = payload.get('webhookEvent', '')
        
        if 'issue' not in payload:
            return {"status": "ignored", "reason": "No issue data"}
        
        issue = payload['issue']
        issue_key = issue.get('key', '')
        fields = issue.get('fields', {})
        
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
        status_jira = fields.get('status', {}).get('name', 'To Do')
        status_map = {
            'To Do': 'Pendente',
            'In Progress': 'Pendente',
            'Done': 'Concluído',
            'Closed': 'Concluído',
            'Aguardando Cliente': 'Aguardando resposta do cliente',
            'Waiting for Customer': 'Aguardando resposta do cliente',
        }
        status = status_map.get(status_jira, 'Pendente')
        
        # Verificar se o caso já existe
        existing_case = await db.cases.find_one({'jira_id': issue_key})
        
        if existing_case:
            # Atualizar caso existente
            update_data = {
                'title': title,
                'description': description,
                'responsible': responsible,
                'status': status
            }
            await db.cases.update_one({'jira_id': issue_key}, {'$set': update_data})
            logger.info(f"Caso atualizado via webhook: {issue_key}")
            return {"status": "updated", "case_id": issue_key}
        else:
            # Criar novo caso
            new_case = Case(
                jira_id=issue_key,
                title=title,
                description=description,
                responsible=responsible,
                status=status
            )
            
            doc = new_case.model_dump()
            doc['opened_date'] = doc['opened_date'].isoformat()
            doc['created_at'] = doc['created_at'].isoformat()
            if doc['closed_date']:
                doc['closed_date'] = doc['closed_date'].isoformat()
            
            await db.cases.insert_one(doc)
            logger.info(f"Novo caso criado via webhook: {issue_key}")
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