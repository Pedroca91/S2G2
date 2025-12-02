import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { AlertTriangle, TrendingUp, Zap, CheckCircle, Clock, AlertCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const COLORS = ['#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9'];

function RecurrentAnalysis() {
  const [recurrentData, setRecurrentData] = useState([]);
  const [categoryStats, setCategoryStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const [recurrentRes, categoryRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/cases/analytics/recurrent`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${BACKEND_URL}/api/cases/categories`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      
      setRecurrentData(recurrentRes.data);
      setCategoryStats(categoryRes.data);
    } catch (error) {
      console.error('Erro ao buscar dados de análise:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (count) => {
    if (count >= 5) return 'bg-red-100 border-red-500 text-red-900';
    if (count >= 3) return 'bg-yellow-100 border-yellow-500 text-yellow-900';
    return 'bg-green-100 border-green-500 text-green-900';
  };

  const getSeverityIcon = (count) => {
    if (count >= 5) return <AlertTriangle className="w-5 h-5 text-red-600" />;
    if (count >= 3) return <AlertCircle className="w-5 h-5 text-yellow-600" />;
    return <CheckCircle className="w-5 h-5 text-green-600" />;
  };

  const chartData = categoryStats.map(cat => ({
    name: cat.category.length > 20 ? cat.category.substring(0, 20) + '...' : cat.category,
    fullName: cat.category,
    total: cat.count,
    concluído: cat.status_breakdown['Concluído'] || 0,
    pendente: cat.status_breakdown['Pendente'] || 0,
    'em desenvolvimento': cat.status_breakdown['Em Desenvolvimento'] || 0,
    aguardando: cat.status_breakdown['Aguardando resposta'] || 0
  }));

  const pieData = categoryStats.map(cat => ({
    name: cat.category,
    value: cat.count
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg p-6 text-white">
        <div className="flex items-center gap-3">
          <TrendingUp className="w-8 h-8" />
          <div>
            <h1 className="text-2xl font-bold">Análise de Casos Recorrentes</h1>
            <p className="text-blue-100">Identificação de padrões e sugestões de automação</p>
          </div>
        </div>
      </div>

      {/* Cards de Alertas Críticos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {recurrentData.slice(0, 3).map((item, index) => (
          <div 
            key={index}
            className={`border-l-4 rounded-lg p-4 shadow-md ${getSeverityColor(item.count)}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {getSeverityIcon(item.count)}
                  <h3 className="font-semibold text-lg">{item.category}</h3>
                </div>
                <div className="space-y-1 text-sm">
                  <p className="font-bold text-2xl">{item.count} casos</p>
                  <p className="opacity-80">{item.percentage}% do total</p>
                </div>
              </div>
              <div className="ml-2">
                {item.count >= 5 && <Zap className="w-6 h-6 text-red-600 animate-pulse" />}
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-current border-opacity-20">
              <p className="text-xs font-medium">{item.suggestion}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico de Barras */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <BarChart className="w-5 h-5" />
            Casos por Categoria
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                      <p className="font-semibold">{payload[0].payload.fullName}</p>
                      <p className="text-sm text-green-600">Concluído: {payload[0].payload.concluído}</p>
                      <p className="text-sm text-yellow-600">Pendente: {payload[0].payload.pendente}</p>
                      <p className="text-sm text-blue-600">Aguardando: {payload[0].payload.aguardando}</p>
                      <p className="text-sm font-bold mt-1">Total: {payload[0].value}</p>
                    </div>
                  );
                }
                return null;
              }} />
              <Legend />
              <Bar dataKey="total" fill="#3b82f6" name="Total de Casos" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Gráfico de Pizza */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold mb-4">Distribuição por Categoria</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Lista Detalhada de Categorias */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold mb-4">Análise Detalhada por Categoria</h2>
        <div className="space-y-3">
          {recurrentData.map((item, index) => (
            <div 
              key={index}
              className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setSelectedCategory(selectedCategory === item.category ? null : item.category)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  {getSeverityIcon(item.count)}
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">{item.category}</h3>
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {item.count} ocorrências
                      </span>
                      <span className="font-medium text-blue-600">{item.percentage}%</span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
                    item.count >= 5 ? 'bg-red-100 text-red-800' :
                    item.count >= 3 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {item.count >= 5 ? 'Crítico' : item.count >= 3 ? 'Atenção' : 'Normal'}
                  </div>
                </div>
              </div>
              
              <div className="mt-3 pt-3 border-t">
                <p className="text-sm text-gray-700">{item.suggestion}</p>
              </div>

              {/* Casos Detalhados */}
              {selectedCategory === item.category && item.cases.length > 0 && (
                <div className="mt-4 space-y-2 border-t pt-3">
                  <h4 className="font-semibold text-sm text-gray-700 mb-2">Casos recentes:</h4>
                  {item.cases.map((caseItem, caseIndex) => (
                    <div key={caseIndex} className="bg-gray-50 rounded p-3 text-sm">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="font-medium text-blue-600">{caseItem.jira_id}</p>
                          <p className="text-gray-800 mt-1">{caseItem.title}</p>
                          <div className="flex items-center gap-3 mt-2 text-xs text-gray-600">
                            <span>👤 {caseItem.responsible}</span>
                            <span>🏢 {caseItem.seguradora || 'N/A'}</span>
                          </div>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          caseItem.status === 'Concluído' ? 'bg-green-100 text-green-800' :
                          caseItem.status === 'Pendente' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {caseItem.status}
                        </span>
                      </div>
                    </div>
                  ))}
                  {item.count > 5 && (
                    <p className="text-xs text-gray-500 text-center pt-2">
                      ... e mais {item.count - 5} casos
                    </p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recomendações de Automação */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg p-6 text-white">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Zap className="w-6 h-6" />
          Recomendações de Automação
        </h2>
        <div className="space-y-3">
          {recurrentData.filter(item => item.count >= 3).map((item, index) => (
            <div key={index} className="bg-white bg-opacity-10 rounded-lg p-4 backdrop-blur">
              <h3 className="font-semibold">{item.category}</h3>
              <p className="text-sm text-blue-100 mt-1">
                Com {item.count} casos ({item.percentage}% do total), recomendamos criar uma automação para este tipo de erro.
              </p>
              {item.count >= 5 && (
                <div className="mt-2 text-xs bg-red-500 bg-opacity-30 rounded px-3 py-1 inline-block">
                  ⚡ PRIORIDADE MÁXIMA
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default RecurrentAnalysis;
