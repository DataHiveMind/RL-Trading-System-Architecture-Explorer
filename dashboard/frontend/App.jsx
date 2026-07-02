import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  AreaChart, Area, BarChart, Bar, ReferenceLine 
} from 'recharts';
import { 
  Activity, DollarSign, TrendingDown, Layers, 
  Target, Percent, ArrowRightLeft, Clock, AlertCircle
} from 'lucide-react';

export default function App() {
  const [telemetry, setTelemetry] = useState({
    portfolio_value: 100000,
    cash: 100000,
    positions: 0,
    current_price: 150,
    max_drawdown: 0,
    step_count: 0,
    sharpe_ratio: 0.0,
    win_rate: 0.0,
    daily_pnl: 0.0
  });
  
  const [history, setHistory] = useState([]);
  const [recentTrades, setRecentTrades] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');

  // --- MOCK DATA STREAM ---
  // In production, this is replaced by the WebSocket connection to your FastAPI backend
  useEffect(() => {
    setConnectionStatus('Connected (Simulated Stream)');
    
    let currentStep = 0;
    let currentValue = 100000;
    let peakValue = 100000;
    let currentPrice = 150;
    let currentWeight = 0; // -1.0 to 1.0
    let wins = 0;
    let totalTrades = 0;

    const interval = setInterval(() => {
      currentStep += 1;
      
      // 1. Simulate Price Movement (Random Walk with slight drift)
      const priceChange = (Math.random() - 0.48) * 2;
      currentPrice += priceChange;

      // 2. Simulate Agent Action (Change Position Weight)
      if (Math.random() > 0.7) { // Agent decides to act 30% of the time
        const oldWeight = currentWeight;
        currentWeight = (Math.random() * 2) - 1; // New weight between -1 and 1
        
        // Log the simulated trade
        totalTrades += 1;
        const isWin = Math.random() > 0.4; // 60% win rate bias for the simulation
        if (isWin) wins++;

        const actionType = currentWeight > oldWeight ? 'BUY' : 'SELL';
        const newTrade = {
          id: `TRD-${Math.floor(Math.random() * 10000)}`,
          step: currentStep,
          action: actionType,
          price: currentPrice.toFixed(2),
          weight: currentWeight.toFixed(2),
          status: 'FILLED'
        };
        
        setRecentTrades(prev => [newTrade, ...prev].slice(0, 8)); // Keep last 8
      }

      // 3. Simulate Portfolio Value based on Price and Weight
      const pnl = currentWeight * priceChange * 100; // Mock multiplier
      currentValue += pnl;
      
      if (currentValue > peakValue) peakValue = currentValue;
      let currentDrawdown = ((peakValue - currentValue) / peakValue) * 100;
      if (currentDrawdown < 0) currentDrawdown = 0;

      // 4. Construct Telemetry Payload
      const newData = {
        portfolio_value: currentValue,
        cash: currentValue * (1 - Math.abs(currentWeight)),
        positions: (currentValue * currentWeight) / currentPrice,
        current_price: currentPrice,
        max_drawdown: currentDrawdown,
        step_count: currentStep,
        sharpe_ratio: 1.2 + (Math.random() * 0.2), // Mock
        win_rate: totalTrades > 0 ? (wins / totalTrades) * 100 : 0,
        daily_pnl: pnl
      };

      setTelemetry(newData);
      
      // Update history arrays for charts
      setHistory(prev => {
        const newHistory = [...prev, { 
          step: newData.step_count, 
          equity: newData.portfolio_value,
          price: newData.current_price,
          drawdown: -newData.max_drawdown, // Negative for underwater chart
          weight: currentWeight
        }];
        return newHistory.length > 60 ? newHistory.slice(1) : newHistory; // 60 ticks rolling window
      });

    }, 800); // Tick every 800ms

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-4 md:p-6 font-sans">
      
      {/* Header */}
      <header className="mb-6 flex flex-col md:flex-row justify-between items-start md:items-center border-b border-gray-800 pb-4 gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="text-blue-500" /> Enterprise QTS Dashboard
          </h1>
          <p className="text-gray-400 mt-1 text-sm">Real-time Reinforcement Learning Telemetry</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right mr-4 hidden md:block">
            <p className="text-xs text-gray-500 uppercase tracking-wider">Active Model</p>
            <p className="text-sm font-mono text-blue-400">PPO-v4_LSTM_Alpha</p>
          </div>
          <div className={`px-3 py-1.5 rounded-full font-semibold text-xs border flex items-center gap-2
            ${connectionStatus.includes('Connected') ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
            <span className={`w-2 h-2 rounded-full ${connectionStatus.includes('Connected') ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`}></span>
            {connectionStatus}
          </div>
        </div>
      </header>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
        <MetricCard title="Total Equity" value={`$${telemetry.portfolio_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`} Icon={DollarSign} color="text-blue-400" />
        <MetricCard title="Daily PnL" value={`$${telemetry.daily_pnl > 0 ? '+' : ''}${telemetry.daily_pnl.toFixed(2)}`} Icon={ArrowRightLeft} color={telemetry.daily_pnl >= 0 ? "text-emerald-400" : "text-red-400"} />
        <MetricCard title="Max Drawdown" value={`${telemetry.max_drawdown.toFixed(2)}%`} Icon={TrendingDown} color="text-orange-400" />
        <MetricCard title="Current Asset Price" value={`$${telemetry.current_price.toFixed(2)}`} Icon={Target} color="text-purple-400" />
        <MetricCard title="Est. Sharpe Ratio" value={telemetry.sharpe_ratio.toFixed(2)} Icon={Activity} color="text-indigo-400" />
        <MetricCard title="Agent Win Rate" value={`${telemetry.win_rate.toFixed(1)}%`} Icon={Percent} color="text-teal-400" />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Big Charts */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Equity Curve */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 shadow-xl">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-200">Portfolio Equity Curve</h2>
              <span className="text-xs font-mono text-gray-500 bg-gray-800 px-2 py-1 rounded">Step: {telemetry.step_count}</span>
            </div>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                  <XAxis dataKey="step" stroke="#6B7280" tick={{fill: '#6B7280', fontSize: 12}} minTickGap={30} />
                  <YAxis domain={['auto', 'auto']} stroke="#6B7280" tick={{fill: '#6B7280', fontSize: 12}} tickFormatter={(val) => `$${(val/1000).toFixed(1)}k`} width={60} />
                  <Tooltip content={<CustomTooltip />} />
                  <Line type="monotone" dataKey="equity" stroke="#3B82F6" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Drawdown Underwater Chart */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 shadow-xl">
              <h2 className="text-lg font-semibold text-gray-200 mb-4 flex items-center gap-2">
                <AlertCircle size={18} className="text-orange-500" /> Risk: Drawdown
              </h2>
              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                    <XAxis dataKey="step" hide />
                    <YAxis domain={[-15, 0]} stroke="#6B7280" tick={{fontSize: 12}} tickFormatter={(val) => `${val}%`} width={40} />
                    <Tooltip contentStyle={{backgroundColor: '#111827', borderColor: '#374151'}} itemStyle={{color: '#F97316'}} formatter={(val) => [`${Number(val).toFixed(2)}%`, 'Drawdown']} labelFormatter={() => ''} />
                    <Area type="monotone" dataKey="drawdown" stroke="#F97316" fill="#7C2D12" fillOpacity={0.3} isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Price Chart */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 shadow-xl">
              <h2 className="text-lg font-semibold text-gray-200 mb-4">Asset Price (Market)</h2>
              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                    <XAxis dataKey="step" hide />
                    <YAxis domain={['auto', 'auto']} stroke="#6B7280" tick={{fontSize: 12}} width={40} />
                    <Tooltip contentStyle={{backgroundColor: '#111827', borderColor: '#374151'}} itemStyle={{color: '#A855F7'}} formatter={(val) => [`$${Number(val).toFixed(2)}`, 'Price']} labelFormatter={() => ''} />
                    <Line type="stepAfter" dataKey="price" stroke="#A855F7" strokeWidth={2} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column: Execution & Logic */}
        <div className="space-y-6">
          
          {/* Agent Position Sizing */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 shadow-xl">
            <h2 className="text-lg font-semibold text-gray-200 mb-4 flex items-center gap-2">
              <Layers size={18} className="text-emerald-500" /> Agent Position Weight
            </h2>
            <div className="h-32 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                  <ReferenceLine y={0} stroke="#4B5563" />
                  <XAxis dataKey="step" hide />
                  <YAxis domain={[-1, 1]} ticks={[-1, 0, 1]} stroke="#6B7280" tick={{fontSize: 12}} width={30} />
                  <Tooltip cursor={{fill: '#1F2937'}} contentStyle={{backgroundColor: '#111827', borderColor: '#374151', color: '#fff'}} formatter={(val) => [Number(val).toFixed(2), 'Weight']} labelFormatter={() => ''}/>
                  <Bar dataKey="weight" isAnimationActive={false}>
                    {history.map((entry, index) => (
                      <cell key={`cell-${index}`} fill={entry.weight >= 0 ? '#10B981' : '#EF4444'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-2 px-8">
              <span>Short (-1.0)</span>
              <span>Neutral</span>
              <span>Long (+1.0)</span>
            </div>
          </div>

          {/* Trade Execution Log */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl shadow-xl overflow-hidden flex flex-col h-[400px]">
            <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-900 z-10">
              <h2 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
                <Clock size={18} className="text-gray-400" /> Execution Tape
              </h2>
            </div>
            <div className="overflow-y-auto flex-1 p-2">
              {recentTrades.length === 0 ? (
                <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                  Waiting for agent actions...
                </div>
              ) : (
                <div className="space-y-2">
                  {recentTrades.map((trade, idx) => (
                    <div key={idx} className="bg-gray-800/50 rounded flex items-center justify-between p-3 text-sm border border-gray-800/80">
                      <div className="flex items-center gap-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${trade.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                          {trade.action}
                        </span>
                        <div>
                          <p className="text-gray-300 font-mono">{trade.id}</p>
                          <p className="text-gray-500 text-xs">Step {trade.step}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-white font-mono">${trade.price}</p>
                        <p className="text-gray-400 text-xs">Wt: {trade.weight}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

// --- SUB-COMPONENTS ---

function MetricCard({ title, value, Icon, color }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 shadow-lg flex flex-col justify-center">
      <div className="flex justify-between items-start mb-2">
        <p className="text-gray-400 text-xs font-semibold uppercase tracking-wider">{title}</p>
        <Icon className={`${color} opacity-80`} size={18} />
      </div>
      <h3 className="text-xl md:text-2xl font-bold text-white tracking-tight">{value}</h3>
    </div>
  );
}

// Custom Tooltip for the main Equity Chart to look professional
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gray-900 border border-gray-700 p-3 rounded shadow-xl">
        <p className="text-gray-400 text-xs mb-1">Step {label}</p>
        <p className="text-blue-400 font-bold font-mono">
          Equity: ${Number(payload[0].value).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
        </p>
      </div>
    );
  }
  return null;
};