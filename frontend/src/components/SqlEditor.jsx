import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Play, 
  RotateCcw, 
  Trash2, 
  CheckCircle2, 
  AlertTriangle, 
  Table as TableIcon, 
  ArrowRight, 
  Loader2, 
  Code2, 
  Clock, 
  Layers,
  Target
} from 'lucide-react';
import { interviewAPI } from '../services/api';
import QuestionSpeaker from './QuestionSpeaker';

const SqlEditor = ({
  question,
  questionNumber = 12,
  totalQuestions = 13,
  sessionId = '',
  onAnswerSubmit = () => {},
  savingAnswer = false,
  isLastQuestion = false
}) => {
  const [query, setQuery] = useState('');
  const [activeTableTab, setActiveTableTab] = useState(0);
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState(null);
  const [lastExecutedQuery, setLastExecutedQuery] = useState('');

  const tables = question?.tables || [];
  
  // Frontend Validation: verify both tables have >= 5 columns and >= 5 rows
  const isSchemaValid = tables.length === 2 && 
    tables.every(t => (t.columns?.length || 0) >= 5 && (t.rows?.length || 0) >= 5);

  useEffect(() => {
    // Reset editor state when question changes
    setQuery('');
    setResult(null);
    setLastExecutedQuery('');
    setActiveTableTab(0);
  }, [question?.id]);

  const handleRunQuery = async () => {
    if (!query.trim() || executing) return;
    setExecuting(true);
    setResult(null);

    try {
      const res = await interviewAPI.runSql(sessionId, question.id, query.trim());
      setResult(res.data);
      setLastExecutedQuery(query.trim());
    } catch (err) {
      setResult({
        success: false,
        error: err.response?.data?.detail || 'Failed to execute query. Check SQL syntax.',
        columns: [],
        rows: [],
        row_count: 0,
        execution_time_ms: 0
      });
    } finally {
      setExecuting(false);
    }
  };

  const handleResetQuery = () => {
    setQuery(`-- Write your MySQL query here\nSELECT * FROM ${tables[0]?.name || 'Employees'};\n`);
    setResult(null);
  };

  const handleClearQuery = () => {
    setQuery('');
    setResult(null);
  };

  const handleKeyDown = (e) => {
    // Run query on Ctrl + Enter or Cmd + Enter
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleRunQuery();
    }
  };

  const handleSubmit = () => {
    onAnswerSubmit(query.trim(), result);
  };

  if (!isSchemaValid) {
    return (
      <div className="glass-card p-6 rounded-3xl border border-rose-800/50 bg-rose-950/20 text-rose-300 space-y-3">
        <div className="flex items-center space-x-2 font-bold">
          <AlertTriangle className="w-5 h-5 text-rose-400" />
          <span>Invalid Database Schema</span>
        </div>
        <p className="text-xs text-rose-300/80">
          This question does not meet the mandatory table schema rules (2 tables with at least 5 columns and 5 rows each).
        </p>
      </div>
    );
  }

  const currentTable = tables[activeTableTab] || tables[0];

  return (
    <div className="space-y-6">
      {/* Question Header Card */}
      <div className="glass-card p-6 rounded-3xl border border-slate-800 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <span className="px-3 py-1 bg-teal-500/20 text-teal-300 border border-teal-500/40 text-xs font-bold rounded-lg uppercase tracking-wider flex items-center space-x-1.5">
              <Database className="w-3.5 h-3.5" />
              <span>SQL Coding Task</span>
            </span>
            <span className="px-2.5 py-1 bg-slate-800 text-slate-300 text-xs font-medium rounded-lg border border-slate-700">
              Topic: {question?.topic || 'SQL Query'}
            </span>
          </div>
          <span className="text-xs font-bold uppercase text-slate-400">
            {question?.difficulty || 'Medium'} Difficulty
          </span>
        </div>

        <div>
          <h3 className="text-xl font-bold text-slate-100 leading-snug">
            {question?.title || 'SQL Problem'}
          </h3>
          <p className="text-sm text-slate-300 mt-2 leading-relaxed font-sans">
            {question?.description || question?.question}
          </p>
        </div>

        {/* Question Speaker TTS Engine & Controls */}
        <QuestionSpeaker
          question={question}
          questionNumber={questionNumber}
          sessionId={sessionId}
          autoSpeak={true}
        />

        {/* Database Tables Preview Tabs */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
              <Layers className="w-3.5 h-3.5 text-blue-400" />
              <span>Available Database Schema (2 Tables)</span>
            </span>
            <span className="text-[11px] text-slate-400 font-mono">
              MySQL 8 Isolated Practice DB
            </span>
          </div>

          <div className="flex space-x-2 border-b border-slate-800 pb-2">
            {tables.map((tbl, idx) => (
              <button
                key={tbl.name}
                type="button"
                onClick={() => setActiveTableTab(idx)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
                  activeTableTab === idx
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                    : 'bg-slate-800/80 text-slate-400 hover:text-slate-200 border border-slate-700/60'
                }`}
              >
                <TableIcon className="w-3.5 h-3.5" />
                <span>{tbl.name}</span>
                <span className="text-[10px] px-1.5 py-0.5 bg-black/30 rounded-md">
                  {tbl.columns.length} cols × {tbl.rows.length} rows
                </span>
              </button>
            ))}
          </div>

          {/* Table Data Preview */}
          <div className="bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden">
            <div className="overflow-x-auto max-h-56">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-900/90 text-slate-300 uppercase sticky top-0 border-b border-slate-800">
                  <tr>
                    {currentTable.columns.map((col) => (
                      <th key={col} className="px-3.5 py-2 font-bold tracking-wider">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {currentTable.rows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-900/50 transition-colors">
                      {currentTable.columns.map((col) => (
                        <td key={col} className="px-3.5 py-1.5 whitespace-nowrap">
                          {row[col] !== null && row[col] !== undefined ? String(row[col]) : <span className="text-slate-600 italic">NULL</span>}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Expected Output Format Card */}
        {(question?.expected_output || question?.expected_result) && (
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3 mt-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                <Target className="w-3.5 h-3.5 text-emerald-400" />
                <span>Expected Output Format</span>
              </span>
              <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                <span className="px-2 py-0.5 bg-emerald-950/50 text-emerald-400 border border-emerald-800/50 rounded-md font-mono">
                  Rows: {question.expected_output?.row_count ?? (question.expected_result?.length || 'Dynamic')}
                </span>
                <span className="px-2 py-0.5 bg-blue-950/50 text-blue-400 border border-blue-800/50 rounded-md font-mono">
                  Cols: {question.expected_output?.columns?.length ?? (question.expected_result?.[0] ? Object.keys(question.expected_result[0]).length : 'Dynamic')}
                </span>
                {question.expected_output?.order_required && (
                  <span className="px-2 py-0.5 bg-amber-950/50 text-amber-400 border border-amber-800/50 rounded-md font-mono">
                    Order: {question.expected_output.ordering || 'Strict'}
                  </span>
                )}
              </div>
            </div>

            {/* Required Columns Pills */}
            {question.expected_output?.columns && (
              <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                <span className="text-[11px] text-slate-400 font-medium mr-1">Required Columns:</span>
                {question.expected_output.columns.map((colName) => (
                  <span key={colName} className="px-2 py-0.5 bg-slate-800 text-slate-200 font-mono text-xs rounded border border-slate-700">
                    {colName}
                  </span>
                ))}
              </div>
            )}

            {/* Notes if present */}
            {question.expected_output?.notes && (
              <p className="text-xs text-slate-400 italic leading-relaxed">
                💡 {question.expected_output.notes}
              </p>
            )}

            {/* Expected Output Example Table Preview */}
            {question.expected_result && question.expected_result.length > 0 && (
              <div className="space-y-1.5 pt-1">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Expected Output Preview ({question.expected_result.length} {question.expected_result.length === 1 ? 'row' : 'rows'}):
                </div>
                <div className="bg-slate-950 rounded-xl border border-slate-800 overflow-hidden">
                  <div className="overflow-x-auto max-h-44">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-slate-900 text-slate-400 uppercase sticky top-0 border-b border-slate-800">
                        <tr>
                          {(question.expected_output?.columns || Object.keys(question.expected_result[0])).map((col) => (
                            <th key={col} className="px-3 py-1.5 font-bold tracking-wider">
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 text-slate-300">
                        {question.expected_result.map((row, rIdx) => (
                          <tr key={rIdx} className="hover:bg-slate-900/40 transition-colors">
                            {(question.expected_output?.columns || Object.keys(row)).map((col) => (
                              <td key={col} className="px-3 py-1.5 whitespace-nowrap">
                                {row[col] !== null && row[col] !== undefined ? String(row[col]) : <span className="text-slate-600 italic">NULL</span>}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* SQL Editor Area */}
      <div className="glass-card p-6 rounded-3xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Code2 className="w-4 h-4 text-blue-400" />
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">SQL Query Editor</h4>
          </div>
          <div className="text-[11px] text-slate-500 font-mono">
            Press <kbd className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">Ctrl + Enter</kbd> to execute
          </div>
        </div>

        {/* Code Input */}
        <div className="relative rounded-2xl overflow-hidden border border-slate-700 bg-slate-950 focus-within:border-blue-500 transition-all">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={7}
            placeholder={`-- Write your MySQL query here\nSELECT * FROM ${tables[0]?.name};\n`}
            className="w-full p-4 bg-transparent text-slate-100 font-mono text-sm leading-relaxed focus:outline-none resize-y"
          />
        </div>

        {/* Toolbar Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={handleRunQuery}
              disabled={executing || !query.trim()}
              className="flex items-center space-x-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl transition-all shadow-lg shadow-emerald-600/20"
            >
              {executing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Executing...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run Query</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleResetQuery}
              className="flex items-center space-x-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-medium border border-slate-700 transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Template</span>
            </button>

            <button
              type="button"
              onClick={handleClearQuery}
              className="flex items-center space-x-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-rose-400 rounded-xl text-xs font-medium border border-slate-700 transition-all"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          </div>
        </div>

        {/* Query Output Section */}
        {result && (
          <div className="space-y-2 pt-2 animate-in fade-in duration-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {result.success ? (
                  <span className="flex items-center space-x-1.5 text-xs font-bold text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Query executed successfully ({result.row_count} rows returned)</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-1.5 text-xs font-bold text-rose-400">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Query Execution Failed</span>
                  </span>
                )}
              </div>
              <span className="text-[11px] text-slate-400 font-mono flex items-center space-x-1">
                <Clock className="w-3 h-3" />
                <span>{result.execution_time_ms} ms</span>
              </span>
            </div>

            {/* Error Display */}
            {!result.success && result.error && (
              <div className="p-3.5 bg-rose-950/40 border border-rose-800/60 rounded-xl text-xs font-mono text-rose-300 whitespace-pre-wrap leading-relaxed">
                {result.error}
              </div>
            )}

            {/* Results Table */}
            {result.success && (
              <div className="bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden max-h-60 overflow-y-auto">
                {result.rows && result.rows.length > 0 ? (
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-900 text-slate-300 uppercase sticky top-0 border-b border-slate-800">
                      <tr>
                        {result.columns.map((c) => (
                          <th key={c} className="px-3.5 py-2 font-bold tracking-wider">
                            {c}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-200">
                      {result.rows.map((r, rIdx) => (
                        <tr key={rIdx} className="hover:bg-slate-900/40 transition-colors">
                          {result.columns.map((c) => (
                            <td key={c} className="px-3.5 py-1.5 whitespace-nowrap">
                              {r[c] !== null && r[c] !== undefined ? String(r[c]) : <span className="text-slate-600 italic">NULL</span>}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="p-6 text-center text-xs text-slate-500 font-mono">
                    Query returned 0 rows.
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Submit / Navigation Action */}
        <div className="flex justify-end pt-4 border-t border-slate-800/80">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={savingAnswer}
            className="px-8 py-3.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold rounded-2xl transition-all shadow-xl shadow-blue-500/25 flex items-center space-x-2"
          >
            <span>
              {savingAnswer ? 'Saving Response...' : (isLastQuestion ? 'Complete Interview' : 'Submit & Next Question')}
            </span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default SqlEditor;
