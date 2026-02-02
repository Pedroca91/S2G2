import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import { Label } from '../components/ui/label';
import { Separator } from '../components/ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { ArrowLeft, MessageSquare, Send, User, Building, AlertCircle, Eye, EyeOff, Calendar, Edit, CheckCircle, FileText, Lightbulb, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CaseDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [state, setState] = useState({
    caseData: null,
    comments: [],
    loading: true,
    commentText: '',
    isInternal: false,
    submitting: false
  });

  const [similarCases, setSimilarCases] = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [expandedSimilar, setExpandedSimilar] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [resolutionDialogOpen, setResolutionDialogOpen] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [resolutionTitle, setResolutionTitle] = useState('');
  const [pendingStatusChange, setPendingStatusChange] = useState(null);
  const [timeMetrics, setTimeMetrics] = useState(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [editFormData, setEditFormData] = useState({
    jira_id: '',
    title: '',
    description: '',
    responsible: '',
    status: 'Pendente',
    priority: 'Média',
    seguradora: '',
    category: ''
  });

  const isAdmin = user?.role === 'administrador';

  const loadData = useCallback(async () => {
    if (!id) return;
    
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [caseRes, commentsRes] = await Promise.all([
        axios.get(`${API}/cases/${id}`, { headers }),
        axios.get(`${API}/cases/${id}/comments`, { headers })
      ]);

      setState(prev => ({
        ...prev,
        caseData: caseRes.data,
        comments: commentsRes.data || [],
        loading: false
      }));

      // Carregar casos similares se não estiver concluído
      if (caseRes.data.status !== 'Concluído') {
        loadSimilarCases(headers);
      }
      
      // Carregar métricas de tempo
      loadTimeMetrics(headers);
    } catch (error) {
      console.error('Erro ao carregar:', error);
      toast.error('Erro ao carregar caso');
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [id]);

  const loadSimilarCases = async (headers) => {
    try {
      setLoadingSimilar(true);
      const token = localStorage.getItem('token');
      const authHeaders = headers || { Authorization: `Bearer ${token}` };
      
      const response = await axios.get(`${API}/cases/${id}/similar`, { headers: authHeaders });
      setSimilarCases(response.data || []);
    } catch (error) {
      console.error('Erro ao carregar casos similares:', error);
    } finally {
      setLoadingSimilar(false);
    }
  };

  const loadTimeMetrics = async (headers) => {
    try {
      setLoadingMetrics(true);
      const token = localStorage.getItem('token');
      const authHeaders = headers || { Authorization: `Bearer ${token}` };
      
      const response = await axios.get(`${API}/cases/${id}/time-metrics`, { headers: authHeaders });
      setTimeMetrics(response.data);
    } catch (error) {
      console.error('Erro ao carregar métricas de tempo:', error);
    } finally {
      setLoadingMetrics(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [loadData]);

  const openEditDialog = () => {
    if (state.caseData) {
      setEditFormData({
        jira_id: state.caseData.jira_id || '',
        title: state.caseData.title || '',
        description: state.caseData.description || '',
        responsible: state.caseData.responsible || '',
        status: state.caseData.status || 'Pendente',
        priority: state.caseData.priority || 'Média',
        seguradora: state.caseData.seguradora || '',
        category: state.caseData.category || ''
      });
      setEditDialogOpen(true);
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    
    // Se o status está mudando para "Concluído" e ainda não tem notas de resolução
    const isChangingToConcluido = editFormData.status === 'Concluído' && state.caseData?.status !== 'Concluído';
    const hasExistingSolution = state.caseData?.solution;
    
    if (isChangingToConcluido && !hasExistingSolution) {
      setPendingStatusChange(editFormData);
      setResolutionDialogOpen(true);
      return;
    }
    
    await submitCaseUpdate(editFormData);
  };

  const submitCaseUpdate = async (formData, solutionData = null) => {
    try {
      const token = localStorage.getItem('token');
      const updateData = { ...formData };
      
      if (solutionData) {
        updateData.solution = solutionData.solution;
        updateData.solved_by = solutionData.solved_by;
        updateData.solved_by_id = solutionData.solved_by_id;
      }
      
      await axios.put(
        `${API}/cases/${id}`,
        updateData,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Caso atualizado com sucesso!');
      setEditDialogOpen(false);
      setResolutionDialogOpen(false);
      setResolutionNotes('');
      setResolutionTitle('');
      setPendingStatusChange(null);
      loadData();
    } catch (error) {
      console.error('Erro:', error);
      toast.error('Erro ao atualizar caso');
    }
  };

  const handleResolutionSubmit = async (e) => {
    e.preventDefault();
    
    if (!resolutionNotes.trim()) {
      toast.error('Por favor, descreva como o caso foi resolvido');
      return;
    }
    
    if (!resolutionTitle.trim()) {
      toast.error('Por favor, informe um título para a solução');
      return;
    }
    
    const solutionData = {
      solution: resolutionNotes,
      solution_title: resolutionTitle,
      solved_by: user?.name || 'Usuário',
      solved_by_id: user?.id || null,
      solved_at: new Date().toISOString()
    };
    
    await submitCaseUpdate(pendingStatusChange, solutionData);
  };

  const handleResolutionCancel = () => {
    setResolutionDialogOpen(false);
    setResolutionNotes('');
    setResolutionTitle('');
    setPendingStatusChange(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!state.commentText.trim() || state.submitting) return;

    setState(prev => ({ ...prev, submitting: true }));
    
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/cases/${id}/comments`,
        { 
          content: state.commentText, 
          is_internal: state.isInternal 
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Comentário adicionado!');
      
      setState(prev => ({
        ...prev,
        commentText: '',
        isInternal: false,
        submitting: false
      }));
      
      loadData();
    } catch (error) {
      console.error('Erro:', error);
      toast.error('Erro ao adicionar comentário');
      setState(prev => ({ ...prev, submitting: false }));
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'Concluído': 'bg-green-100 text-green-800 border-green-300',
      'Pendente': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'Em Desenvolvimento': 'bg-blue-100 text-blue-800 border-blue-300',
      'Aguardando resposta': 'bg-orange-100 text-orange-800 border-orange-300',
      'Aguardando Configuração': 'bg-cyan-100 text-cyan-800 border-cyan-300'
    };
    return colors[status] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  if (state.loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (!state.caseData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">Chamado não encontrado</p>
          <Button onClick={() => navigate('/cases')}>Voltar</Button>
        </div>
      </div>
    );
  }

  const { caseData, comments, commentText, isInternal, submitting } = state;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-5xl mx-auto">
        <Button variant="ghost" onClick={() => navigate('/cases')} className="mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Voltar
        </Button>

        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-2xl font-bold">{caseData.title}</h1>
                <Badge className={getStatusColor(caseData.status)}>
                  {caseData.status}
                </Badge>
              </div>
              <p className="text-sm text-gray-600">
                Chamado #{caseData.jira_id || caseData.id?.substring(0, 8)}
              </p>
            </div>
            
            {isAdmin && (
              <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
                <DialogTrigger asChild>
                  <Button
                    variant="outline"
                    onClick={openEditDialog}
                    className="flex items-center gap-2"
                  >
                    <Edit className="h-4 w-4" />
                    Editar Chamado
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Editar Chamado</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleEditSubmit} className="space-y-4 mt-4">
                    <div>
                      <Label htmlFor="edit_jira_id">ID do Jira</Label>
                      <Input
                        id="edit_jira_id"
                        value={editFormData.jira_id}
                        onChange={(e) => setEditFormData({ ...editFormData, jira_id: e.target.value })}
                        placeholder="Ex: SUP-123"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="edit_title">Título</Label>
                      <Input
                        id="edit_title"
                        value={editFormData.title}
                        onChange={(e) => setEditFormData({ ...editFormData, title: e.target.value })}
                        required
                        placeholder="Título do chamado"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="edit_description">Descrição</Label>
                      <Textarea
                        id="edit_description"
                        value={editFormData.description}
                        onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                        required
                        placeholder="Descreva o chamado"
                        rows={4}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="edit_responsible">Responsável</Label>
                      <Input
                        id="edit_responsible"
                        value={editFormData.responsible}
                        onChange={(e) => setEditFormData({ ...editFormData, responsible: e.target.value })}
                        placeholder="Nome do responsável"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="edit_status">Status</Label>
                      <Select
                        value={editFormData.status}
                        onValueChange={(value) => setEditFormData({ ...editFormData, status: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Pendente">🟡 Pendente</SelectItem>
                          <SelectItem value="Em Desenvolvimento">🔵 Em Desenvolvimento</SelectItem>
                          <SelectItem value="Aguardando resposta">🟠 Aguardando resposta</SelectItem>
                          <SelectItem value="Aguardando Configuração">⚙️ Aguardando Configuração</SelectItem>
                          <SelectItem value="Concluído">🟢 Concluído</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="edit_priority">Prioridade</Label>
                      <Select
                        value={editFormData.priority}
                        onValueChange={(value) => setEditFormData({ ...editFormData, priority: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Baixa">🟢 Baixa</SelectItem>
                          <SelectItem value="Média">🟡 Média</SelectItem>
                          <SelectItem value="Alta">🟠 Alta</SelectItem>
                          <SelectItem value="Urgente">🔴 Urgente</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="edit_seguradora">Seguradora</Label>
                      <Select
                        value={editFormData.seguradora}
                        onValueChange={(value) => setEditFormData({ ...editFormData, seguradora: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione a seguradora" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Nenhuma">Nenhuma</SelectItem>
                          <SelectItem value="AVLA">AVLA</SelectItem>
                          <SelectItem value="DAYCOVAL">DAYCOVAL</SelectItem>
                          <SelectItem value="ESSOR">ESSOR</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="edit_category">Categoria</Label>
                      <Select
                        value={editFormData.category}
                        onValueChange={(value) => setEditFormData({ ...editFormData, category: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione a categoria" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Nenhuma">Nenhuma</SelectItem>
                          <SelectItem value="Erro Técnico">Erro Técnico</SelectItem>
                          <SelectItem value="Erro Boleto">Erro Boleto</SelectItem>
                          <SelectItem value="Erro Corretor">Erro Corretor</SelectItem>
                          <SelectItem value="Problema Documento">Problema Documento</SelectItem>
                          <SelectItem value="Reprocessamento">Reprocessamento</SelectItem>
                          <SelectItem value="Cobertura">Cobertura</SelectItem>
                          <SelectItem value="Sumiço de Dados">Sumiço de Dados</SelectItem>
                          <SelectItem value="Adequação Nova Lei">Adequação Nova Lei</SelectItem>
                          <SelectItem value="Outros">Outros</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="flex gap-2 justify-end pt-4">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setEditDialogOpen(false)}
                      >
                        Cancelar
                      </Button>
                      <Button 
                        type="submit"
                        className="bg-purple-600 hover:bg-purple-700"
                      >
                        Salvar Alterações
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            )}

            {/* Modal de Notas de Resolução */}
            <Dialog open={resolutionDialogOpen} onOpenChange={setResolutionDialogOpen}>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    Notas de Resolução
                  </DialogTitle>
                </DialogHeader>
                <form onSubmit={handleResolutionSubmit} className="space-y-4 mt-4">
                  <p className="text-sm text-gray-600">
                    Antes de concluir este caso, descreva como ele foi resolvido. Isso ajudará a criar uma base de conhecimento para resolver problemas semelhantes no futuro.
                  </p>
                  <div>
                    <Label htmlFor="resolution_title">Título da Solução *</Label>
                    <Input
                      id="resolution_title"
                      value={resolutionTitle}
                      onChange={(e) => setResolutionTitle(e.target.value)}
                      placeholder="Ex: Correção de boleto com código de barras inválido"
                      className="mt-2"
                      required
                      data-testid="resolution-title-input"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Um título claro facilita encontrar esta solução na Base de Conhecimento
                    </p>
                  </div>
                  <div>
                    <Label htmlFor="resolution_notes">Como o caso foi resolvido? *</Label>
                    <Textarea
                      id="resolution_notes"
                      value={resolutionNotes}
                      onChange={(e) => setResolutionNotes(e.target.value)}
                      placeholder="Descreva a solução aplicada, passos seguidos, configurações alteradas, etc."
                      rows={5}
                      className="mt-2"
                      required
                      data-testid="resolution-notes-textarea"
                    />
                  </div>
                  <div className="flex gap-2 justify-end pt-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleResolutionCancel}
                    >
                      Cancelar
                    </Button>
                    <Button 
                      type="submit"
                      className="bg-green-600 hover:bg-green-700"
                      disabled={!resolutionNotes.trim() || !resolutionTitle.trim()}
                      data-testid="submit-resolution-btn"
                    >
                      <CheckCircle className="mr-2 h-4 w-4" />
                      Concluir Caso
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          <Separator className="my-4" />

          {/* Seção de Notas de Resolução (quando concluído) */}
          {caseData.status === 'Concluído' && caseData.solution && (
            <>
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4" data-testid="resolution-info-section">
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="h-5 w-5 text-green-600" />
                  <h3 className="font-semibold text-green-800">Notas de Resolução</h3>
                </div>
                {caseData.solution_title && (
                  <h4 className="text-lg font-medium text-green-900 mb-2">
                    {caseData.solution_title}
                  </h4>
                )}
                <p className="text-gray-700 whitespace-pre-wrap bg-white p-3 rounded border border-green-100">
                  {caseData.solution}
                </p>
                {caseData.solved_by && (
                  <p className="text-sm text-green-700 mt-2">
                    <span className="font-medium">Resolvido por:</span> {caseData.solved_by}
                  </p>
                )}
              </div>
              <Separator className="my-4" />
            </>
          )}

          {/* Seção de Casos Similares Resolvidos */}
          {caseData.status !== 'Concluído' && similarCases.length > 0 && (
            <>
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4" data-testid="similar-cases-section">
                <div className="flex items-center gap-2 mb-3">
                  <Lightbulb className="h-5 w-5 text-amber-600" />
                  <h3 className="font-semibold text-amber-800">
                    Casos Similares Resolvidos ({similarCases.length})
                  </h3>
                </div>
                <p className="text-sm text-amber-700 mb-4">
                  Encontramos casos similares que já foram resolvidos. Verifique se alguma solução pode ajudar:
                </p>
                
                <div className="space-y-3">
                  {similarCases.map((similar) => (
                    <div 
                      key={similar.id}
                      className={`bg-white rounded-lg border transition-all ${
                        expandedSimilar === similar.id 
                          ? 'border-amber-400 shadow-md' 
                          : 'border-amber-200 hover:border-amber-300'
                      }`}
                    >
                      <div 
                        className="p-3 cursor-pointer"
                        onClick={() => setExpandedSimilar(expandedSimilar === similar.id ? null : similar.id)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1 flex-wrap">
                              <span className="text-xs font-medium text-amber-600 bg-amber-100 px-2 py-0.5 rounded">
                                {similar.jira_id}
                              </span>
                              {similar.category && (
                                <Badge variant="outline" className="text-xs">
                                  {similar.category}
                                </Badge>
                              )}
                              <span className="text-xs text-gray-500">
                                {similar.similarity_score}% similar
                              </span>
                            </div>
                            <h4 className="font-medium text-gray-900 text-sm">
                              {similar.solution_title || similar.title}
                            </h4>
                            {similar.matching_keywords?.length > 0 && (
                              <p className="text-xs text-gray-500 mt-1">
                                Palavras em comum: {similar.matching_keywords.join(', ')}
                              </p>
                            )}
                          </div>
                          <Button variant="ghost" size="sm" className="ml-2">
                            {expandedSimilar === similar.id ? (
                              <ChevronUp className="h-4 w-4" />
                            ) : (
                              <ChevronDown className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </div>
                      
                      {expandedSimilar === similar.id && (
                        <div className="px-3 pb-3 border-t border-amber-100 pt-3 bg-amber-50/50">
                          <div className="mb-3">
                            <h5 className="text-xs font-semibold text-amber-700 mb-1 flex items-center gap-1">
                              <CheckCircle className="w-3 h-3" />
                              Solução Aplicada
                            </h5>
                            <p className="text-sm text-gray-700 bg-white p-2 rounded border border-amber-100 whitespace-pre-wrap">
                              {similar.solution}
                            </p>
                          </div>
                          {similar.solved_by && (
                            <p className="text-xs text-gray-500 mb-2">
                              Resolvido por: {similar.solved_by}
                            </p>
                          )}
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/cases/${similar.id}`);
                            }}
                            className="text-amber-600 border-amber-300 hover:bg-amber-50"
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            Ver Caso Completo
                          </Button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
              <Separator className="my-4" />
            </>
          )}

          {/* Loading de casos similares */}
          {caseData.status !== 'Concluído' && loadingSimilar && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-amber-600"></div>
                <span className="text-sm text-gray-600">Buscando casos similares...</span>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {caseData.seguradora && (
              <div className="flex items-center gap-2 text-sm">
                <Building className="h-4 w-4 text-gray-500" />
                <span className="text-gray-600">Seguradora:</span>
                <span className="font-medium">{caseData.seguradora}</span>
              </div>
            )}

            <div className="flex items-center gap-2 text-sm">
              <User className="h-4 w-4 text-gray-500" />
              <span className="text-gray-600">Responsável:</span>
              <span className="font-medium">{caseData.responsible || 'Não atribuído'}</span>
            </div>

            {caseData.priority && (
              <div className="flex items-center gap-2 text-sm">
                <AlertCircle className="h-4 w-4 text-gray-500" />
                <span className="text-gray-600">Prioridade:</span>
                <span className={`font-medium ${
                  caseData.priority === 'Urgente' ? 'text-red-600' :
                  caseData.priority === 'Alta' ? 'text-orange-600' :
                  caseData.priority === 'Média' ? 'text-yellow-600' :
                  'text-green-600'
                }`}>
                  {caseData.priority}
                </span>
              </div>
            )}

            {caseData.category && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-600">Categoria:</span>
                <span className="font-medium">{caseData.category}</span>
              </div>
            )}

            <div className="flex items-center gap-2 text-sm">
              <Calendar className="h-4 w-4 text-gray-500" />
              <span className="text-gray-600">Aberto em:</span>
              <span className="font-medium">{formatDate(caseData.opened_date)}</span>
            </div>

            {caseData.creator_name && (
              <div className="flex items-center gap-2 text-sm">
                <User className="h-4 w-4 text-gray-500" />
                <span className="text-gray-600">Criado por:</span>
                <span className="font-medium">{caseData.creator_name}</span>
              </div>
            )}
          </div>

          <Separator className="my-4" />

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Descrição</h3>
            <p className="text-gray-700 whitespace-pre-wrap bg-gray-50 p-4 rounded-lg">
              {caseData.description || 'Sem descrição'}
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Comentários ({comments.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 mb-6">
              {comments.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Nenhum comentário</p>
                </div>
              ) : (
                comments.map((comment, idx) => (
                  <div 
                    key={`comment-${comment.id || idx}-${idx}`}
                    className={`p-4 rounded-lg border ${
                      comment.is_internal 
                        ? 'bg-amber-50 border-amber-200' 
                        : 'bg-white border-gray-200'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                          {comment.user_name?.charAt(0).toUpperCase() || '?'}
                        </div>
                        <div>
                          <p className="font-semibold text-sm">{comment.user_name || 'Usuário'}</p>
                          <p className="text-xs text-gray-500">{formatDate(comment.created_at)}</p>
                        </div>
                      </div>
                      
                      {comment.is_internal && (
                        <Badge variant="outline" className="bg-amber-100 text-amber-800">
                          <EyeOff className="h-3 w-3 mr-1" />
                          Interno
                        </Badge>
                      )}
                    </div>
                    <p className="text-gray-700 whitespace-pre-wrap ml-10">{comment.content}</p>
                  </div>
                ))
              )}
            </div>

            <Separator className="my-6" />

            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="comment">Adicionar Comentário</Label>
                  <Textarea
                    id="comment"
                    placeholder="Escreva sua resposta..."
                    value={commentText}
                    onChange={(e) => setState(prev => ({ ...prev, commentText: e.target.value }))}
                    rows={4}
                    className="mt-2"
                  />
                </div>

                {isAdmin && (
                  <div className="flex items-center space-x-2 bg-amber-50 p-3 rounded-lg border border-amber-200">
                    <Switch
                      id="internal"
                      checked={isInternal}
                      onCheckedChange={(checked) => setState(prev => ({ ...prev, isInternal: checked }))}
                    />
                    <Label htmlFor="internal" className="cursor-pointer flex items-center gap-2">
                      {isInternal ? (
                        <>
                          <EyeOff className="h-4 w-4" />
                          <span>Comentário Interno</span>
                        </>
                      ) : (
                        <>
                          <Eye className="h-4 w-4" />
                          <span>Comentário Público</span>
                        </>
                      )}
                    </Label>
                  </div>
                )}

                <div className="flex justify-end">
                  <Button 
                    type="submit" 
                    disabled={submitting || !commentText.trim()}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    <Send className="mr-2 h-4 w-4" />
                    {submitting ? 'Enviando...' : 'Enviar'}
                  </Button>
                </div>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CaseDetails;