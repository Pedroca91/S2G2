import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Plus, Search, Edit, Trash2, Filter, Wifi, WifiOff, Eye, Info } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Cases = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [cases, setCases] = useState([]);
  const [filteredCases, setFilteredCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCase, setEditingCase] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [responsibleFilter, setResponsibleFilter] = useState('all');
  const [seguradoraFilter, setSeguradoraFilter] = useState('all');
  const [newCaseIds, setNewCaseIds] = useState(new Set());
  const [soundEnabled, setSoundEnabled] = useState(false);
  const audioContextRef = useRef(null);
  const isAdmin = user?.role === 'administrador';
  const [formData, setFormData] = useState({
    jira_id: '',
    title: '',
    description: '',
    responsible: '',
    status: 'Pendente',
    seguradora: '',
  });

  // Inicializar AudioContext na primeira interação do usuário
  const enableSound = async () => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }
      
      // Tocar um som de teste
      const oscillator = audioContextRef.current.createOscillator();
      const gainNode = audioContextRef.current.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContextRef.current.destination);
      
      oscillator.frequency.value = 800;
      gainNode.gain.value = 0.1;
      
      oscillator.start();
      oscillator.stop(audioContextRef.current.currentTime + 0.1);
      
      setSoundEnabled(true);
      toast.success('🔔 Notificações sonoras ativadas!');
    } catch (error) {
      console.error('Erro ao habilitar som:', error);
      toast.error('Erro ao ativar som');
    }
  };

  // Função melhorada para tocar som
  const playSound = () => {
    if (!soundEnabled || !audioContextRef.current) {
      console.log('Som não habilitado ainda');
      return;
    }

    try {
      const ctx = audioContextRef.current;
      
      // Primeiro tom (800Hz)
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      
      osc1.connect(gain1);
      gain1.connect(ctx.destination);
      
      osc1.type = 'sine';
      osc1.frequency.value = 800;
      gain1.gain.setValueAtTime(0.3, ctx.currentTime);
      gain1.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
      
      osc1.start(ctx.currentTime);
      osc1.stop(ctx.currentTime + 0.3);
      
      // Segundo tom (1000Hz) - após 100ms
      setTimeout(() => {
        const osc2 = ctx.createOscillator();
        const gain2 = ctx.createGain();
        
        osc2.connect(gain2);
        gain2.connect(ctx.destination);
        
        osc2.type = 'sine';
        osc2.frequency.value = 1000;
        gain2.gain.setValueAtTime(0.3, ctx.currentTime);
        gain2.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
        
        osc2.start(ctx.currentTime);
        osc2.stop(ctx.currentTime + 0.2);
      }, 100);
      
      console.log('🔔 Som tocado com sucesso!');
    } catch (error) {
      console.error('Erro ao tocar som:', error);
    }
  };

  // WebSocket handler
  const handleWebSocketMessage = (data) => {
    if (data.type === 'new_case') {
      console.log('🆕 Novo caso recebido via WebSocket:', data.case);
      
      // Adicionar novo caso à lista
      setCases(prevCases => [data.case, ...prevCases]);
      
      // Marcar como novo
      setNewCaseIds(prev => new Set([...prev, data.case.id]));
      
      // Remover badge "NOVO" após 30 segundos
      setTimeout(() => {
        setNewCaseIds(prev => {
          const newSet = new Set(prev);
          newSet.delete(data.case.id);
          return newSet;
        });
      }, 30000);
      
      // Tocar som (função melhorada)
      playSound();
      
      // Mostrar toast
      toast.success('🆕 Novo caso do Jira!', {
        description: `${data.case.jira_id}: ${data.case.title}`,
        duration: 5000
      });
      
      // Notificação do navegador
      showBrowserNotification('Novo Caso Safe2Go', {
        body: `${data.case.jira_id}: ${data.case.title}`,
        tag: data.case.id
      });
    } else if (data.type === 'case_updated') {
      console.log('🔄 Caso atualizado via WebSocket:', data.case_id);
      
      // Recarregar casos
      fetchCases();
      
      // Mostrar toast
      toast.info('🔄 Caso atualizado', {
        description: `${data.case_id} foi atualizado`
      });
    }
  };

  const { isConnected } = useWebSocket(handleWebSocketMessage);

  // Solicitar permissão de notificação ao montar
  useEffect(() => {
    requestNotificationPermission();
  }, []);

  useEffect(() => {
    fetchCases();
    
    // Aplicar filtros da URL se existirem
    const statusFromUrl = searchParams.get('status');
    const seguradoraFromUrl = searchParams.get('seguradora');
    
    if (statusFromUrl) {
      setStatusFilter(statusFromUrl);
      toast.info(`Filtrando por status: ${statusFromUrl}`);
    }
    
    if (seguradoraFromUrl) {
      setSeguradoraFilter(seguradoraFromUrl);
      toast.success(`📊 Mostrando casos da ${seguradoraFromUrl}`, {
        duration: 3000
      });
    }
  }, []);

  // Recarregar casos quando a página receber foco
  useEffect(() => {
    const handleFocus = () => {
      fetchCases();
    };
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, []);

  useEffect(() => {
    filterCases();
  }, [cases, searchTerm, statusFilter, responsibleFilter, seguradoraFilter]);

  const fetchCases = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/cases`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCases(response.data);
    } catch (error) {
      console.error('Erro ao carregar casos:', error);
      toast.error('Erro ao carregar casos');
    } finally {
      setLoading(false);
    }
  };

  const filterCases = () => {
    let filtered = [...cases];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (c) =>
          c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.jira_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.responsible.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((c) => c.status === statusFilter);
    }

    // Responsible filter
    if (responsibleFilter !== 'all') {
      filtered = filtered.filter((c) => c.responsible === responsibleFilter);
    }

    // Seguradora filter
    if (seguradoraFilter !== 'all') {
      filtered = filtered.filter((c) => c.seguradora === seguradoraFilter);
    }

    setFilteredCases(filtered);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingCase) {
        await axios.put(`${API}/cases/${editingCase.id}`, formData);
        toast.success('✅ Caso atualizado e salvo no banco de dados!');
      } else {
        await axios.post(`${API}/cases`, formData);
        toast.success('Caso criado com sucesso!');
      }
      setDialogOpen(false);
      resetForm();
      fetchCases();
    } catch (error) {
      console.error('Erro ao salvar caso:', error);
      toast.error('Erro ao salvar caso');
    }
  };

  const handleEdit = (caseItem) => {
    setEditingCase(caseItem);
    setFormData({
      jira_id: caseItem.jira_id,
      title: caseItem.title,
      description: caseItem.description,
      responsible: caseItem.responsible,
      status: caseItem.status,
      seguradora: caseItem.seguradora || '',
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Tem certeza que deseja deletar este caso?')) {
      try {
        await axios.delete(`${API}/cases/${id}`);
        toast.success('Caso deletado com sucesso!');
        fetchCases();
      } catch (error) {
        console.error('Erro ao deletar caso:', error);
        toast.error('Erro ao deletar caso');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      jira_id: '',
      title: '',
      description: '',
      responsible: '',
      status: 'Pendente',
      seguradora: '',
    });
    setEditingCase(null);
  };

  const uniqueResponsibles = [...new Set(cases.map((c) => c.responsible))];

  return (
    <div className="page-container">
      <div className="page-header flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="page-title" data-testid="cases-title">Casos</h1>
            {/* Indicador de conexão WebSocket */}
            <div className="flex items-center gap-2">
              {isConnected ? (
                <div className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                  <Wifi className="w-3 h-3" />
                  <span>Ao vivo</span>
                </div>
              ) : (
                <div className="flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium">
                  <WifiOff className="w-3 h-3" />
                  <span>Desconectado</span>
                </div>
              )}
              
              {/* Botão para habilitar som */}
              {!soundEnabled && isConnected && (
                <button
                  onClick={enableSound}
                  className="flex items-center gap-1 px-3 py-1 bg-yellow-100 text-yellow-700 hover:bg-yellow-200 rounded-full text-xs font-medium transition-colors"
                  title="Clique para ativar notificações sonoras"
                >
                  🔔 Ativar Som
                </button>
              )}
              
              {soundEnabled && (
                <div className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                  🔔 Som Ativo
                </div>
              )}
            </div>
          </div>
          <p className="page-subtitle">Gerencie todos os casos de suporte</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) resetForm();
        }}>
          <DialogTrigger asChild>
            <Button
              data-testid="add-case-btn"
              className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white shadow-lg"
            >
              <Plus className="w-4 h-4 mr-2" />
              Novo Caso
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingCase ? 'Editar Caso' : 'Novo Caso'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4 mt-4">
              <div>
                <Label htmlFor="jira_id">ID do Jira</Label>
                <Input
                  id="jira_id"
                  data-testid="jira-id-input"
                  value={formData.jira_id}
                  onChange={(e) => setFormData({ ...formData, jira_id: e.target.value })}
                  required
                  placeholder="Ex: SUP-123"
                />
              </div>
              <div>
                <Label htmlFor="title">Título</Label>
                <Input
                  id="title"
                  data-testid="title-input"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  placeholder="Título do caso"
                />
              </div>
              <div>
                <Label htmlFor="description">Descrição</Label>
                <Textarea
                  id="description"
                  data-testid="description-input"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                  placeholder="Descreva o caso"
                  rows={4}
                />
              </div>
              <div>
                <Label htmlFor="responsible">Responsável</Label>
                <Input
                  id="responsible"
                  data-testid="responsible-input"
                  value={formData.responsible}
                  onChange={(e) => setFormData({ ...formData, responsible: e.target.value })}
                  required
                  placeholder="Nome do responsável"
                />
              </div>
              <div>
                <Label htmlFor="seguradora">Seguradora</Label>
                <Select
                  value={formData.seguradora}
                  onValueChange={(value) => setFormData({ ...formData, seguradora: value })}
                >
                  <SelectTrigger data-testid="seguradora-select">
                    <SelectValue placeholder="Selecione a seguradora" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="AVLA">AVLA</SelectItem>
                    <SelectItem value="DAYCOVAL">DAYCOVAL</SelectItem>
                    <SelectItem value="ESSOR">ESSOR</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="status">Status</Label>
                <Select
                  value={formData.status}
                  onValueChange={(value) => setFormData({ ...formData, status: value })}
                >
                  <SelectTrigger data-testid="status-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Pendente">Pendente</SelectItem>
                    <SelectItem value="Concluído">Concluído</SelectItem>
                    <SelectItem value="Aguardando resposta do cliente">Aguardando resposta do cliente</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2 justify-end">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setDialogOpen(false);
                    resetForm();
                  }}
                  data-testid="cancel-btn"
                >
                  Cancelar
                </Button>
                <Button type="submit" data-testid="save-case-btn">
                  {editingCase ? 'Atualizar' : 'Criar'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Banner informativo para clientes */}
      {!isAdmin && (
        <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-blue-900 mb-1">Meus Chamados</h3>
              <p className="text-sm text-blue-800">
                Aqui você pode ver todos os seus chamados e acompanhar o andamento. 
                Para abrir um novo chamado, clique no botão "Abrir Chamado" no topo da página.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <Label htmlFor="search" className="flex items-center gap-2 mb-2">
              <Search className="w-4 h-4" />
              Buscar
            </Label>
            <Input
              id="search"
              data-testid="search-input"
              placeholder="Buscar por título, ID ou responsável"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="status-filter" className="flex items-center gap-2 mb-2">
              <Filter className="w-4 h-4" />
              Status
            </Label>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger id="status-filter" data-testid="status-filter">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                <SelectItem value="Pendente">Pendente</SelectItem>
                <SelectItem value="Concluído">Concluído</SelectItem>
                <SelectItem value="Aguardando resposta do cliente">Aguardando resposta do cliente</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="responsible-filter" className="flex items-center gap-2 mb-2">
              <Filter className="w-4 h-4" />
              Responsável
            </Label>
            <Select value={responsibleFilter} onValueChange={setResponsibleFilter}>
              <SelectTrigger id="responsible-filter" data-testid="responsible-filter">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                {uniqueResponsibles.map((resp) => (
                  <SelectItem key={resp} value={resp}>
                    {resp}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="seguradora-filter" className="flex items-center gap-2 mb-2">
              <Filter className="w-4 h-4" />
              Seguradora
            </Label>
            <Select value={seguradoraFilter} onValueChange={setSeguradoraFilter}>
              <SelectTrigger id="seguradora-filter" data-testid="seguradora-filter">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas</SelectItem>
                <SelectItem value="AVLA">AVLA</SelectItem>
                <SelectItem value="ESSOR">ESSOR</SelectItem>
                <SelectItem value="DAYCOVAL">DAYCOVAL</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Indicador de Filtro Ativo */}
      {seguradoraFilter !== 'all' && (
        <div className="mb-4 bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-purple-700 font-medium">
                📊 Filtrando por: {seguradoraFilter}
              </span>
              <span className="text-purple-600 text-sm">
                ({filteredCases.length} {filteredCases.length === 1 ? 'caso' : 'casos'})
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSeguradoraFilter('all');
                setSearchParams({});
                toast.success('Filtro removido');
              }}
              className="text-purple-600 border-purple-300 hover:bg-purple-100"
            >
              Limpar Filtro
            </Button>
          </div>
        </div>
      )}

      {/* Cases List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Carregando...</div>
        </div>
      ) : filteredCases.length === 0 ? (
        <div className="card text-center py-12" data-testid="no-cases-message">
          <p className="text-gray-500">Nenhum caso encontrado</p>
        </div>
      ) : (
        <div className="grid gap-4" data-testid="cases-list">
          {filteredCases.map((caseItem) => (
            <div
              key={caseItem.id}
              data-testid={`case-item-${caseItem.id}`}
              className="card hover:shadow-lg transition-shadow"
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2 flex-wrap">
                    <span className="text-sm font-medium text-purple-600 bg-purple-50 px-3 py-1 rounded-lg">
                      {caseItem.jira_id}
                    </span>
                    {/* Badge NOVO para casos recém-criados */}
                    {newCaseIds.has(caseItem.id) && (
                      <span className="animate-pulse flex items-center gap-1 px-2 py-1 bg-red-500 text-white rounded-full text-xs font-bold">
                        🔴 NOVO
                      </span>
                    )}
                    <span
                      className={`badge ${
                        caseItem.status === 'Concluído' 
                          ? 'badge-success' 
                          : caseItem.status === 'Aguardando resposta do cliente'
                          ? 'badge-waiting'
                          : 'badge-pending'
                      }`}
                      data-testid={`case-status-${caseItem.id}`}
                    >
                      {caseItem.status}
                    </span>
                    {caseItem.category && (
                      <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded-md border border-blue-200">
                        📂 {caseItem.category}
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{caseItem.title}</h3>
                  <p className="text-sm text-gray-600 mb-2">{caseItem.description}</p>
                  <div className="flex items-center gap-4 text-sm text-gray-500 flex-wrap">
                    <span>Responsável: <strong>{caseItem.responsible}</strong></span>
                    {caseItem.seguradora && (
                      <span className="inline-flex items-center px-2 py-1 bg-purple-100 text-purple-700 rounded-md text-xs font-medium">
                        {caseItem.seguradora}
                      </span>
                    )}
                    <span>Aberto: {new Date(caseItem.opened_date).toLocaleDateString('pt-BR')}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => navigate(`/cases/${caseItem.id}`)}
                    data-testid={`view-case-${caseItem.id}`}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    Ver Detalhes
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(caseItem)}
                    data-testid={`edit-case-${caseItem.id}`}
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(caseItem.id)}
                    data-testid={`delete-case-${caseItem.id}`}
                    className="text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Cases;