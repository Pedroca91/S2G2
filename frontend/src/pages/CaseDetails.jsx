import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import { Label } from '../components/ui/label';
import { Separator } from '../components/ui/separator';
import { 
  ArrowLeft, 
  MessageSquare, 
  Send, 
  Clock, 
  User, 
  Building,
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  Calendar
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CaseDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [caseData, setCaseData] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [commentText, setCommentText] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const isAdmin = user?.role === 'administrador';

  // Ref para controlar se o componente está montado
  const isMountedRef = React.useRef(true);

  useEffect(() => {
    isMountedRef.current = true;

    const loadData = async () => {
      try {
        const token = localStorage.getItem('token');
        
        // Buscar caso
        const caseResponse = await axios.get(`${API}/cases/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (isMountedRef.current) {
          setCaseData(caseResponse.data);
        }

        // Buscar comentários
        const commentsResponse = await axios.get(`${API}/cases/${id}/comments`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (isMountedRef.current) {
          setComments(commentsResponse.data);
        }
      } catch (error) {
        console.error('Erro ao carregar dados:', error);
        if (isMountedRef.current) {
          toast.error('Erro ao carregar detalhes do caso');
        }
      } finally {
        if (isMountedRef.current) {
          setLoading(false);
        }
      }
    };

    loadData();

    // Cleanup function
    return () => {
      isMountedRef.current = false;
    };
  }, [id]);

  const fetchComments = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/cases/${id}/comments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setComments(response.data);
    } catch (error) {
      console.error('Erro ao carregar comentários:', error);
    }
  };

  const handleSubmitComment = async (e) => {
    e.preventDefault();
    
    if (!commentText.trim()) {
      toast.error('Digite um comentário');
      return;
    }

    if (submitting) {
      return; // Prevenir múltiplos submits
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/cases/${id}/comments`,
        {
          content: commentText,
          is_internal: isInternal
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Comentário adicionado!');
      setCommentText('');
      setIsInternal(false);
      
      // Aguardar um pouco antes de recarregar
      setTimeout(() => {
        fetchComments();
      }, 300);
    } catch (error) {
      console.error('Erro ao adicionar comentário:', error);
      toast.error('Erro ao adicionar comentário');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'Concluído': 'bg-green-100 text-green-800 border-green-300',
      'Pendente': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'Aguardando resposta do cliente': 'bg-blue-100 text-blue-800 border-blue-300'
    };
    return colors[status] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      'Urgente': 'bg-red-100 text-red-800',
      'Alta': 'bg-orange-100 text-orange-800',
      'Média': 'bg-yellow-100 text-yellow-800',
      'Baixa': 'bg-green-100 text-green-800'
    };
    return colors[priority] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString('pt-BR', {
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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando...</p>
        </div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600">Caso não encontrado</p>
          <Button onClick={() => navigate('/cases')} className="mt-4">
            Voltar para Casos
          </Button>
        </div>
      </div>
    );
  }

  // Garantir que temos dados antes de renderizar
  if (!caseData.id || !caseData.title) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-gray-600">Dados inválidos</p>
          <Button onClick={() => navigate('/cases')} className="mt-4">
            Voltar para Casos
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/cases')}
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Voltar para Casos
          </Button>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-2xl font-bold text-gray-900">{caseData.title}</h1>
                  <Badge className={getStatusColor(caseData.status)}>
                    {caseData.status}
                  </Badge>
                </div>
                <p className="text-gray-600 text-sm">
                  Chamado #{caseData.jira_id || caseData.id.substring(0, 8)}
                </p>
              </div>
              
              {caseData.priority && (
                <Badge className={getPriorityColor(caseData.priority)}>
                  {caseData.priority}
                </Badge>
              )}
            </div>

            <Separator className="my-4" />

            {/* Informações do Caso */}
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

              <div className="flex items-center gap-2 text-sm">
                <Calendar className="h-4 w-4 text-gray-500" />
                <span className="text-gray-600">Aberto em:</span>
                <span className="font-medium">{caseData.opened_date ? formatDate(caseData.opened_date) : 'Data não disponível'}</span>
              </div>

              {caseData.creator_name && (
                <div className="flex items-center gap-2 text-sm">
                  <User className="h-4 w-4 text-gray-500" />
                  <span className="text-gray-600">Criado por:</span>
                  <span className="font-medium">{caseData.creator_name}</span>
                </div>
              )}

              {caseData.category && (
                <div className="flex items-center gap-2 text-sm">
                  <AlertCircle className="h-4 w-4 text-gray-500" />
                  <span className="text-gray-600">Categoria:</span>
                  <span className="font-medium">{caseData.category}</span>
                </div>
              )}

              {caseData.closed_date && (
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  <span className="text-gray-600">Fechado em:</span>
                  <span className="font-medium">{formatDate(caseData.closed_date)}</span>
                </div>
              )}
            </div>

            <Separator className="my-4" />

            {/* Descrição */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Descrição</h3>
              <p className="text-gray-700 whitespace-pre-wrap bg-gray-50 p-4 rounded-lg">
                {caseData.description || 'Sem descrição'}
              </p>
            </div>
          </div>
        </div>

        {/* Comentários */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Comentários ({comments.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* Lista de Comentários */}
            <div className="space-y-4 mb-6">
              {!comments || comments.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Nenhum comentário ainda</p>
                  <p className="text-sm">Seja o primeiro a comentar!</p>
                </div>
              ) : (
                comments.filter(c => c && c.id).map((comment, index) => (
                  <div 
                    key={`comment-${comment.id}-${index}`} 
                    className={`p-4 rounded-lg border ${
                      comment.is_internal 
                        ? 'bg-amber-50 border-amber-200' 
                        : 'bg-white border-gray-200'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                          {comment.user_name ? comment.user_name.charAt(0).toUpperCase() : '?'}
                        </div>
                        <div>
                          <p className="font-semibold text-sm">{comment.user_name || 'Usuário'}</p>
                          <p className="text-xs text-gray-500">
                            {formatDate(comment.created_at)}
                          </p>
                        </div>
                      </div>
                      
                      {comment.is_internal && (
                        <Badge variant="outline" className="bg-amber-100 text-amber-800 border-amber-300">
                          <EyeOff className="h-3 w-3 mr-1" />
                          Interno
                        </Badge>
                      )}
                    </div>
                    <p className="text-gray-700 whitespace-pre-wrap ml-10">
                      {comment.content}
                    </p>
                  </div>
                ))
              )}
            </div>

            <Separator className="my-6" />

            {/* Formulário de Novo Comentário */}
            <form onSubmit={handleSubmitComment}>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="comment">Adicionar Comentário</Label>
                  <Textarea
                    id="comment"
                    placeholder={
                      isInternal 
                        ? "Escreva uma observação interna (apenas para administradores)..." 
                        : "Escreva sua resposta ou atualização..."
                    }
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    rows={4}
                    className="mt-2"
                  />
                </div>

                {isAdmin && (
                  <div className="flex items-center space-x-2 bg-amber-50 p-3 rounded-lg border border-amber-200">
                    <Switch
                      id="internal"
                      checked={isInternal}
                      onCheckedChange={setIsInternal}
                    />
                    <Label htmlFor="internal" className="cursor-pointer flex items-center gap-2">
                      {isInternal ? (
                        <>
                          <EyeOff className="h-4 w-4 text-amber-600" />
                          <span className="text-amber-800">Comentário Interno (só administradores veem)</span>
                        </>
                      ) : (
                        <>
                          <Eye className="h-4 w-4 text-gray-600" />
                          <span>Comentário Público (cliente verá)</span>
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
                    {submitting ? 'Enviando...' : 'Enviar Comentário'}
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
