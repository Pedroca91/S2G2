import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, BookOpen, Filter, ChevronDown, ChevronUp, ExternalLink, Calendar, User, Tag, Building } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const KnowledgeBase = () => {
  const navigate = useNavigate();
  const [notes, setNotes] = useState([]);
  const [stats, setStats] = useState({ total: 0, by_category: [], by_seguradora: [] });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [seguradoraFilter, setSeguradoraFilter] = useState('all');
  const [expandedNote, setExpandedNote] = useState(null);

  useEffect(() => {
    fetchData();
  }, [categoryFilter, seguradoraFilter]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const params = new URLSearchParams();
      if (categoryFilter !== 'all') params.append('category', categoryFilter);
      if (seguradoraFilter !== 'all') params.append('seguradora', seguradoraFilter);

      const [notesRes, statsRes] = await Promise.all([
        axios.get(`${API}/knowledge-base?${params.toString()}`, { headers }),
        axios.get(`${API}/knowledge-base/stats`, { headers })
      ]);

      setNotes(notesRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Erro ao carregar base de conhecimento:', error);
      toast.error('Erro ao carregar base de conhecimento');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (categoryFilter !== 'all') params.append('category', categoryFilter);
      if (seguradoraFilter !== 'all') params.append('seguradora', seguradoraFilter);

      const response = await axios.get(`${API}/knowledge-base?${params.toString()}`, { headers });
      setNotes(response.data);
      
      if (searchTerm && response.data.length === 0) {
        toast.info(`Nenhuma solução encontrada para "${searchTerm}"`);
      } else if (searchTerm) {
        toast.success(`${response.data.length} solução(ões) encontrada(s)`);
      }
    } catch (error) {
      console.error('Erro na busca:', error);
      toast.error('Erro ao buscar');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Erro Boleto': 'bg-red-100 text-red-700',
      'Erro Corretor': 'bg-orange-100 text-orange-700',
      'Reprocessamento': 'bg-blue-100 text-blue-700',
      'Problema Documento': 'bg-yellow-100 text-yellow-700',
      'Adequação Nova Lei': 'bg-purple-100 text-purple-700',
      'Sumiço de Dados': 'bg-pink-100 text-pink-700',
      'Integração': 'bg-cyan-100 text-cyan-700',
      'Erro Técnico': 'bg-gray-100 text-gray-700',
    };
    return colors[category] || 'bg-gray-100 text-gray-700';
  };

  const uniqueCategories = [...new Set(stats.by_category.map(c => c.category))];
  const uniqueSeguradoras = [...new Set(stats.by_seguradora.map(s => s.seguradora))];

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header mb-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl shadow-lg">
            <BookOpen className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="page-title" data-testid="knowledge-base-title">Base de Conhecimento</h1>
            <p className="page-subtitle">Soluções documentadas para problemas recorrentes</p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600 font-medium">Total de Soluções</p>
                <p className="text-3xl font-bold text-green-700">{stats.total}</p>
              </div>
              <BookOpen className="h-10 w-10 text-green-500 opacity-50" />
            </div>
          </CardContent>
        </Card>

        {stats.by_category.slice(0, 3).map((cat, idx) => (
          <Card key={idx} className="bg-white">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{cat.category || 'Outros'}</p>
                  <p className="text-2xl font-bold text-gray-800">{cat.count}</p>
                </div>
                <Tag className="h-8 w-8 text-gray-400" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Search and Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-2">
              <Label className="flex items-center gap-2 mb-2">
                <Search className="w-4 h-4" />
                Buscar Solução
              </Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Digite palavras-chave (ex: boleto, endosso, corretor...)"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={handleKeyPress}
                  data-testid="knowledge-search-input"
                  className="flex-1"
                />
                <Button 
                  onClick={handleSearch}
                  className="bg-green-600 hover:bg-green-700"
                  data-testid="knowledge-search-btn"
                >
                  <Search className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <div>
              <Label className="flex items-center gap-2 mb-2">
                <Filter className="w-4 h-4" />
                Categoria
              </Label>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger data-testid="category-filter">
                  <SelectValue placeholder="Todas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas as categorias</SelectItem>
                  {uniqueCategories.map((cat) => (
                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="flex items-center gap-2 mb-2">
                <Building className="w-4 h-4" />
                Seguradora
              </Label>
              <Select value={seguradoraFilter} onValueChange={setSeguradoraFilter}>
                <SelectTrigger data-testid="seguradora-filter">
                  <SelectValue placeholder="Todas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas as seguradoras</SelectItem>
                  {uniqueSeguradoras.map((seg) => (
                    <SelectItem key={seg} value={seg}>{seg}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        </div>
      ) : notes.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <BookOpen className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg">Nenhuma solução encontrada</p>
            <p className="text-gray-400 text-sm mt-2">
              {searchTerm ? 'Tente buscar com outras palavras-chave' : 'Resolva chamados para criar a base de conhecimento'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4" data-testid="knowledge-base-list">
          <p className="text-sm text-gray-500 mb-2">
            {notes.length} solução(ões) encontrada(s)
          </p>
          
          {notes.map((note) => (
            <Card 
              key={note.id} 
              className={`transition-all hover:shadow-md ${expandedNote === note.id ? 'ring-2 ring-green-500' : ''}`}
              data-testid={`knowledge-item-${note.id}`}
            >
              <CardContent className="p-0">
                {/* Header - Always visible */}
                <div 
                  className="p-4 cursor-pointer"
                  onClick={() => setExpandedNote(expandedNote === note.id ? null : note.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <span className="text-sm font-medium text-green-600 bg-green-50 px-2 py-1 rounded">
                          {note.jira_id}
                        </span>
                        {note.category && (
                          <Badge className={getCategoryColor(note.category)}>
                            {note.category}
                          </Badge>
                        )}
                        {note.seguradora && (
                          <Badge variant="outline" className="text-purple-600 border-purple-300">
                            {note.seguradora}
                          </Badge>
                        )}
                      </div>
                      
                      {/* Solution Title */}
                      <h3 className="text-lg font-semibold text-gray-900 mb-1">
                        {note.solution_title || note.title}
                      </h3>
                      
                      {/* Original case title if different */}
                      {note.solution_title && note.solution_title !== note.title && (
                        <p className="text-sm text-gray-500 mb-2">
                          Chamado: {note.title}
                        </p>
                      )}

                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {note.solved_by || 'Não informado'}
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDate(note.solved_at)}
                        </span>
                      </div>
                    </div>
                    
                    <Button variant="ghost" size="sm">
                      {expandedNote === note.id ? (
                        <ChevronUp className="h-5 w-5" />
                      ) : (
                        <ChevronDown className="h-5 w-5" />
                      )}
                    </Button>
                  </div>
                </div>

                {/* Expanded Content */}
                {expandedNote === note.id && (
                  <div className="px-4 pb-4 border-t border-gray-100 pt-4 bg-gray-50">
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Descrição do Problema</h4>
                      <p className="text-gray-600 text-sm bg-white p-3 rounded border">
                        {note.description || 'Sem descrição'}
                      </p>
                    </div>
                    
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-green-700 mb-2 flex items-center gap-2">
                        <BookOpen className="w-4 h-4" />
                        Solução Aplicada
                      </h4>
                      <div className="text-gray-700 bg-green-50 p-4 rounded-lg border border-green-200 whitespace-pre-wrap">
                        {note.solution}
                      </div>
                    </div>

                    <div className="flex justify-end">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(`/cases/${note.id}`)}
                        className="text-green-600 border-green-300 hover:bg-green-50"
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        Ver Chamado Completo
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default KnowledgeBase;
