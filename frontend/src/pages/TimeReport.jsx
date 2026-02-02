import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Clock, Timer, Download, Filter, TrendingUp, TrendingDown, AlertCircle, CheckCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TimeReport = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState(null);
  const [cases, setCases] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const casesPerPage = 10;

  // Filtros
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setMonth(date.getMonth() - 1);
    return date.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [seguradora, setSeguradora] = useState('all');
  const [category, setCategory] = useState('all');

  const [categories, setCategories] = useState([]);
  const [seguradoras, setSeguradoras] = useState([]);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      // Buscar categorias e seguradoras para os filtros
      const [casesRes] = await Promise.all([
        axios.get(`${API}/cases`, { headers })
      ]);

      const allCases = casesRes.data;
      const uniqueCategories = [...new Set(allCases.map(c => c.category).filter(Boolean))];
      const uniqueSeguradoras = [...new Set(allCases.map(c => c.seguradora).filter(Boolean))];

      setCategories(uniqueCategories);
      setSeguradoras(uniqueSeguradoras);

      // Buscar métricas iniciais
      await fetchMetrics();
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      toast.error('Erro ao carregar dados');
      setLoading(false);
    }
  };

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (seguradora && seguradora !== 'all') params.append('seguradora', seguradora);

      const response = await axios.get(`${API}/reports/time-metrics?${params.toString()}`, { headers });
      setMetrics(response.data);

      // Filtrar casos para a tabela
      let filteredCases = response.data.cases_by_resolution_time || [];
      if (category && category !== 'all') {
        // Buscar casos completos para filtrar por categoria
        const casesRes = await axios.get(`${API}/cases`, { headers });
        const completedCases = casesRes.data.filter(c => c.status === 'Concluído');
        
        filteredCases = completedCases
          .filter(c => {
            const matchCategory = !category || category === 'all' || c.category === category;
            const matchSeguradora = !seguradora || seguradora === 'all' || c.seguradora === seguradora;
            return matchCategory && matchSeguradora;
          })
          .map(c => ({
            case_id: c.id,
            jira_id: c.jira_id,
            title: c.title,
            category: c.category,
            seguradora: c.seguradora,
            resolution_seconds: calculateResolutionTime(c),
            resolution_formatted: formatDuration(calculateResolutionTime(c))
          }))
          .sort((a, b) => a.resolution_seconds - b.resolution_seconds);
      }

      setCases(filteredCases);
      setCurrentPage(1);
    } catch (error) {
      console.error('Erro ao buscar métricas:', error);
      toast.error('Erro ao buscar métricas');
    } finally {
      setLoading(false);
    }
  };

  const calculateResolutionTime = (caseData) => {
    const created = new Date(caseData.created_at);
    const closed = new Date(caseData.closed_date || caseData.solved_at || caseData.updated_at);
    return Math.floor((closed - created) / 1000);
  };

  const formatDuration = (seconds) => {
    if (!seconds || seconds <= 0) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}min`;
    return `${minutes}min`;
  };

  const handleApplyFilters = () => {
    fetchMetrics();
    toast.success('Filtros aplicados');
  };

  const exportToExcel = () => {
    if (!cases || cases.length === 0) {
      toast.error('Não há dados para exportar');
      return;
    }

    // Criar CSV
    const headers = ['Caso', 'Título', 'Categoria', 'Seguradora', 'Tempo de Resolução'];
    const rows = cases.map(c => [
      c.jira_id || c.case_id,
      `"${(c.title || '').replace(/"/g, '""')}"`,
      c.category || '',
      c.seguradora || '',
      c.resolution_formatted || ''
    ]);

    const csv = [headers.join(';'), ...rows.map(r => r.join(';'))].join('\n');
    
    // Download
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `relatorio-tempo-${startDate}-${endDate}.csv`;
    link.click();

    toast.success('Relatório exportado com sucesso!');
  };

  // Paginação
  const totalPages = Math.ceil((cases?.length || 0) / casesPerPage);
  const paginatedCases = cases?.slice(
    (currentPage - 1) * casesPerPage,
    currentPage * casesPerPage
  ) || [];

  const getStatusColor = (status) => {
    const colors = {
      'Pendente': 'bg-yellow-100 text-yellow-700',
      'Em Desenvolvimento': 'bg-blue-100 text-blue-700',
      'Aguardando resposta': 'bg-orange-100 text-orange-700',
      'Aguardando Configuração': 'bg-cyan-100 text-cyan-700',
      'Concluído': 'bg-green-100 text-green-700'
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  const getCategoryColor = (cat) => {
    const colors = {
      'Erro Boleto': 'bg-red-100 text-red-700',
      'Reprocessamento': 'bg-blue-100 text-blue-700',
      'Integração': 'bg-purple-100 text-purple-700',
      'Configuração': 'bg-cyan-100 text-cyan-700',
      'Erro Corretor': 'bg-orange-100 text-orange-700'
    };
    return colors[cat] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header mb-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg">
            <Clock className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="page-title" data-testid="time-report-title">Relatório de Tempo</h1>
            <p className="page-subtitle">Análise detalhada de tempo de resolução dos chamados</p>
          </div>
        </div>
      </div>

      {/* Filtros */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Filter className="w-4 h-4 text-gray-500" />
            <h3 className="font-semibold text-gray-700">Filtros</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <Label className="text-sm text-gray-600 mb-1 block">Data Início</Label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                data-testid="start-date-filter"
              />
            </div>
            <div>
              <Label className="text-sm text-gray-600 mb-1 block">Data Fim</Label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                data-testid="end-date-filter"
              />
            </div>
            <div>
              <Label className="text-sm text-gray-600 mb-1 block">Seguradora</Label>
              <Select value={seguradora} onValueChange={setSeguradora}>
                <SelectTrigger data-testid="seguradora-filter">
                  <SelectValue placeholder="Todas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {seguradoras.map((seg) => (
                    <SelectItem key={seg} value={seg}>{seg}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-sm text-gray-600 mb-1 block">Categoria</Label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger data-testid="category-filter">
                  <SelectValue placeholder="Todas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button 
                onClick={handleApplyFilters}
                className="w-full bg-indigo-600 hover:bg-indigo-700"
                data-testid="apply-filters-btn"
              >
                Aplicar Filtros
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      ) : (
        <>
          {/* Cards de Resumo */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card className="border-t-4 border-indigo-500">
              <CardContent className="p-4">
                <p className="text-gray-500 text-sm">Casos Analisados</p>
                <p className="text-3xl font-bold text-gray-800">{metrics?.total_cases || 0}</p>
              </CardContent>
            </Card>

            <Card className="border-t-4 border-blue-500">
              <CardContent className="p-4">
                <p className="text-gray-500 text-sm">Tempo Médio de Resolução</p>
                <p className="text-3xl font-bold text-blue-600">
                  {metrics?.avg_resolution_time_formatted || 'N/A'}
                </p>
              </CardContent>
            </Card>

            <Card className="border-t-4 border-green-500">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-500 text-sm">Resolução Mais Rápida</p>
                    <p className="text-2xl font-bold text-green-600">
                      {metrics?.fastest_case?.resolution_formatted || 'N/A'}
                    </p>
                    {metrics?.fastest_case && (
                      <p className="text-xs text-gray-500 mt-1">{metrics.fastest_case.jira_id}</p>
                    )}
                  </div>
                  <TrendingDown className="h-5 w-5 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-t-4 border-red-500">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-500 text-sm">Resolução Mais Lenta</p>
                    <p className="text-2xl font-bold text-red-600">
                      {metrics?.slowest_case?.resolution_formatted || 'N/A'}
                    </p>
                    {metrics?.slowest_case && (
                      <p className="text-xs text-gray-500 mt-1">{metrics.slowest_case.jira_id}</p>
                    )}
                  </div>
                  <TrendingUp className="h-5 w-5 text-red-500" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Gráficos */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {/* Tempo Médio por Status */}
            <Card>
              <CardContent className="p-4">
                <h3 className="font-semibold text-gray-700 mb-4 flex items-center gap-2">
                  <Timer className="w-4 h-4" />
                  Tempo Médio por Status
                </h3>
                {metrics?.time_by_status_avg?.length > 0 ? (
                  <div className="space-y-3">
                    {metrics.time_by_status_avg.map((item, idx) => {
                      const maxTime = Math.max(...metrics.time_by_status_avg.map(i => i.avg_seconds || 0));
                      const percentage = maxTime > 0 ? ((item.avg_seconds || 0) / maxTime) * 100 : 0;
                      
                      const statusColors = {
                        'Pendente': 'bg-yellow-500',
                        'Em Desenvolvimento': 'bg-blue-500',
                        'Aguardando resposta': 'bg-orange-500',
                        'Aguardando Configuração': 'bg-cyan-500'
                      };
                      const barColor = statusColors[item.status] || 'bg-gray-500';

                      return (
                        <div key={idx}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">{item.status}</span>
                            <span className="font-medium">{item.avg_formatted}</span>
                          </div>
                          <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
                            <div 
                              className={`h-full ${barColor} rounded-full transition-all duration-500`}
                              style={{ width: `${percentage}%` }}
                            ></div>
                          </div>
                          <p className="text-xs text-gray-400 mt-1">{item.count} casos</p>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">Sem dados de histórico de status</p>
                )}
              </CardContent>
            </Card>

            {/* Distribuição por Faixa de Tempo */}
            <Card>
              <CardContent className="p-4">
                <h3 className="font-semibold text-gray-700 mb-4 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Distribuição por Faixa de Tempo
                </h3>
                {metrics?.time_distribution?.length > 0 ? (
                  <div className="space-y-3">
                    {metrics.time_distribution.map((item, idx) => {
                      const total = metrics.total_cases || 1;
                      const percentage = ((item.count / total) * 100).toFixed(0);
                      
                      const rangeColors = [
                        'bg-green-500',    // < 1h
                        'bg-lime-500',     // 1-4h
                        'bg-yellow-500',   // 4-8h
                        'bg-orange-500',   // 8-24h
                        'bg-red-500'       // > 24h
                      ];
                      const textColors = [
                        'text-green-600',
                        'text-lime-600',
                        'text-yellow-600',
                        'text-orange-600',
                        'text-red-600'
                      ];

                      return (
                        <div key={idx}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className={`font-medium ${textColors[idx]}`}>{item.range}</span>
                            <span className="font-bold">{item.count} casos ({percentage}%)</span>
                          </div>
                          <div className="h-6 bg-gray-100 rounded overflow-hidden">
                            <div 
                              className={`h-full ${rangeColors[idx]} rounded flex items-center justify-end pr-2 transition-all duration-500`}
                              style={{ width: `${Math.max(percentage, 5)}%` }}
                            >
                              {percentage > 10 && (
                                <span className="text-white text-xs font-bold">{percentage}%</span>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">Sem dados de distribuição</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Tabela Detalhada */}
          <Card>
            <CardContent className="p-0">
              <div className="p-4 border-b flex justify-between items-center">
                <h3 className="font-semibold text-gray-700 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Detalhamento por Caso
                </h3>
                <Button 
                  onClick={exportToExcel}
                  className="bg-green-600 hover:bg-green-700"
                  data-testid="export-excel-btn"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Exportar Excel
                </Button>
              </div>

              {cases?.length > 0 ? (
                <>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="text-left p-3 text-sm font-medium text-gray-600">Caso</th>
                          <th className="text-left p-3 text-sm font-medium text-gray-600">Título</th>
                          <th className="text-left p-3 text-sm font-medium text-gray-600">Categoria</th>
                          <th className="text-left p-3 text-sm font-medium text-gray-600">Seguradora</th>
                          <th className="text-left p-3 text-sm font-medium text-gray-600">Tempo Total</th>
                          <th className="text-left p-3 text-sm font-medium text-gray-600">Ações</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {paginatedCases.map((caseItem, idx) => {
                          // Determinar cor baseado no tempo
                          const seconds = caseItem.resolution_seconds || 0;
                          let timeColor = 'text-green-600';
                          let rowBg = '';
                          if (seconds > 28800) { // > 8h
                            timeColor = 'text-red-600';
                            rowBg = 'bg-red-50';
                          } else if (seconds > 14400) { // > 4h
                            timeColor = 'text-yellow-600';
                          }

                          return (
                            <tr key={idx} className={`hover:bg-gray-50 ${rowBg}`}>
                              <td className="p-3 text-sm font-medium text-blue-600">
                                {caseItem.jira_id || caseItem.case_id?.substring(0, 8)}
                              </td>
                              <td className="p-3 text-sm text-gray-700 max-w-xs truncate">
                                {caseItem.title || 'Sem título'}
                              </td>
                              <td className="p-3">
                                {caseItem.category && (
                                  <Badge className={getCategoryColor(caseItem.category)}>
                                    {caseItem.category}
                                  </Badge>
                                )}
                              </td>
                              <td className="p-3 text-sm text-gray-600">
                                {caseItem.seguradora || '-'}
                              </td>
                              <td className={`p-3 text-sm font-bold ${timeColor}`}>
                                {caseItem.resolution_formatted}
                              </td>
                              <td className="p-3">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => navigate(`/cases/${caseItem.case_id}`)}
                                >
                                  Ver
                                </Button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Paginação */}
                  {totalPages > 1 && (
                    <div className="p-3 border-t flex items-center justify-between">
                      <p className="text-sm text-gray-500">
                        Mostrando {((currentPage - 1) * casesPerPage) + 1} - {Math.min(currentPage * casesPerPage, cases.length)} de {cases.length} casos
                      </p>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                          disabled={currentPage === 1}
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </Button>
                        <span className="text-sm text-gray-600">
                          Página {currentPage} de {totalPages}
                        </span>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                          disabled={currentPage === totalPages}
                        >
                          <ChevronRight className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="p-8 text-center text-gray-500">
                  <Clock className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>Nenhum caso concluído encontrado no período selecionado</p>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};

export default TimeReport;
