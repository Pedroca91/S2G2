import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { Send, ArrowLeft, Building, AlertCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const NewTicket = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'Média',
    seguradora: '',
    category: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title.trim() || !formData.description.trim()) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      
      // Gerar um ID temporário para o Jira
      const tempJiraId = `WEB-${Date.now().toString().slice(-6)}`;
      
      await axios.post(
        `${API}/cases`,
        {
          jira_id: tempJiraId,
          title: formData.title,
          description: formData.description,
          priority: formData.priority,
          seguradora: formData.seguradora || null,
          category: formData.category || null,
          status: 'Pendente',
          responsible: 'Não atribuído'
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Chamado criado com sucesso!');
      navigate('/cases');
    } catch (error) {
      console.error('Erro ao criar chamado:', error);
      toast.error(error.response?.data?.detail || 'Erro ao criar chamado');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-3xl mx-auto">
        <Button 
          variant="ghost" 
          onClick={() => navigate('/cases')}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Voltar
        </Button>

        <Card>
          <CardHeader className="bg-gradient-to-r from-purple-600 to-blue-600 text-white">
            <CardTitle className="text-2xl flex items-center gap-2">
              <Send className="h-6 w-6" />
              Abrir Novo Chamado
            </CardTitle>
            <CardDescription className="text-purple-100">
              Descreva seu problema ou solicitação detalhadamente
            </CardDescription>
          </CardHeader>
          
          <CardContent className="mt-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Título */}
              <div>
                <Label htmlFor="title" className="text-base font-semibold">
                  Título do Chamado *
                </Label>
                <p className="text-sm text-gray-600 mb-2">
                  Resuma o problema em poucas palavras
                </p>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Ex: Erro ao gerar boleto na plataforma"
                  required
                  className="text-base"
                />
              </div>

              {/* Descrição */}
              <div>
                <Label htmlFor="description" className="text-base font-semibold">
                  Descrição Detalhada *
                </Label>
                <p className="text-sm text-gray-600 mb-2">
                  Explique o problema, quando ocorreu, e o que você já tentou fazer
                </p>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Descreva aqui todos os detalhes do seu problema..."
                  required
                  rows={6}
                  className="text-base"
                />
              </div>

              {/* Prioridade */}
              <div>
                <Label htmlFor="priority" className="text-base font-semibold">
                  Prioridade
                </Label>
                <p className="text-sm text-gray-600 mb-2">
                  Quão urgente é este problema?
                </p>
                <Select value={formData.priority} onValueChange={(value) => setFormData({ ...formData, priority: value })}>
                  <SelectTrigger id="priority">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Baixa">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-green-500"></div>
                        Baixa - Pode aguardar
                      </div>
                    </SelectItem>
                    <SelectItem value="Média">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                        Média - Normal
                      </div>
                    </SelectItem>
                    <SelectItem value="Alta">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                        Alta - Preciso de atenção
                      </div>
                    </SelectItem>
                    <SelectItem value="Urgente">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-red-500"></div>
                        Urgente - Sistema parado
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Seguradora */}
              <div>
                <Label htmlFor="seguradora" className="text-base font-semibold flex items-center gap-2">
                  <Building className="h-4 w-4" />
                  Seguradora (opcional)
                </Label>
                <p className="text-sm text-gray-600 mb-2">
                  Se o problema está relacionado a uma seguradora específica
                </p>
                <Select value={formData.seguradora} onValueChange={(value) => setFormData({ ...formData, seguradora: value })}>
                  <SelectTrigger id="seguradora">
                    <SelectValue placeholder="Selecione uma seguradora" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Nenhuma</SelectItem>
                    <SelectItem value="AVLA">AVLA</SelectItem>
                    <SelectItem value="ESSOR">ESSOR</SelectItem>
                    <SelectItem value="DAYCOVAL">DAYCOVAL</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Categoria */}
              <div>
                <Label htmlFor="category" className="text-base font-semibold flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  Categoria (opcional)
                </Label>
                <p className="text-sm text-gray-600 mb-2">
                  Tipo de problema ou solicitação
                </p>
                <Select value={formData.category} onValueChange={(value) => setFormData({ ...formData, category: value })}>
                  <SelectTrigger id="category">
                    <SelectValue placeholder="Selecione uma categoria" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Nenhuma</SelectItem>
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

              {/* Informações do Usuário */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">Suas Informações</h3>
                <div className="space-y-1 text-sm text-blue-800">
                  <p><strong>Nome:</strong> {user?.name}</p>
                  <p><strong>Email:</strong> {user?.email}</p>
                  {user?.company && <p><strong>Empresa:</strong> {user?.company}</p>}
                </div>
              </div>

              {/* Botões */}
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/cases')}
                  className="flex-1"
                  disabled={submitting}
                >
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                >
                  <Send className="mr-2 h-4 w-4" />
                  {submitting ? 'Enviando...' : 'Enviar Chamado'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default NewTicket;
