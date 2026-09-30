import React from 'react';
import { CheckCircle2, Code2, ArrowRight, HelpCircle, Terminal } from 'lucide-react';
import QuestionSpeaker from './QuestionSpeaker';

const PseudocodeMcqQuestion = ({
  question,
  questionNumber = 10,
  totalQuestions = 13,
  sessionId = '',
  selectedOptionId = null,
  onSelectOption = () => {},
  onNextQuestion = () => {},
  savingAnswer = false,
  isLastQuestion = false,
  isAITtsSpeaking = false,
  setIsAITtsSpeaking = () => {}
}) => {
  const pseudocodeText = question?.pseudocode || question?.code_snippet || '';
  const inputText = question?.input || question?.input_description || 'No external input.';
  const options = question?.options || [];

  return (
    <div className="space-y-6">
      {/* Top Question Card */}
      <div className="glass-card p-6 rounded-3xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="px-3 py-1 text-xs font-bold rounded-lg uppercase tracking-wider bg-purple-600/20 text-purple-300 border border-purple-500/30 flex items-center space-x-1.5">
              <Code2 className="w-3.5 h-3.5 mr-1" />
              PSEUDOCODE MCQ • {question?.category || 'LOGIC'}
            </span>
            <span className="px-2.5 py-0.5 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-md">
              Objective MCQ
            </span>
          </div>
          <span className="text-xs font-semibold text-slate-400 uppercase">
            {question?.difficulty || 'medium'} Difficulty
          </span>
        </div>

        <div>
          <h3 className="text-xl font-bold text-slate-100 leading-snug">
            {question?.question || 'What is the output of the following pseudocode?'}
          </h3>
          {question?.topic && (
            <p className="text-xs text-slate-400 mt-1">
              Topic: <span className="text-slate-300 font-medium">{question.topic}</span>
            </p>
          )}
        </div>

        {/* Pseudocode Box */}
        {pseudocodeText && (
          <div className="space-y-1.5 pt-1">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1">
                <Terminal className="w-3.5 h-3.5 text-purple-400 mr-1" />
                Language-Independent Pseudocode:
              </span>
            </div>
            <pre className="p-4 bg-slate-950 rounded-2xl border border-purple-950/60 text-xs font-mono text-purple-200 overflow-x-auto whitespace-pre-wrap leading-relaxed shadow-inner">
              <code>{pseudocodeText}</code>
            </pre>
          </div>
        )}

        {/* Input Details */}
        {inputText && (
          <div className="bg-slate-950/80 p-3.5 rounded-2xl border border-slate-800 flex items-start space-x-2.5">
            <div className="p-1 rounded-lg bg-blue-500/10 text-blue-400 shrink-0 mt-0.5">
              <HelpCircle className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Input Values / State:
              </span>
              <p className="text-xs text-slate-200 font-mono mt-0.5 leading-relaxed">
                {inputText}
              </p>
            </div>
          </div>
        )}

        {/* Question Speaker TTS */}
        <QuestionSpeaker
          question={question}
          questionNumber={questionNumber}
          sessionId={sessionId}
          autoSpeak={true}
          onSpeechStart={() => setIsAITtsSpeaking(true)}
          onSpeechEnd={() => setIsAITtsSpeaking(false)}
          onSpeechError={() => setIsAITtsSpeaking(false)}
        />
      </div>

      {/* Options Selection Card */}
      <div className="glass-card p-6 rounded-3xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
            <span>Choose the correct output:</span>
          </h4>
          <span className="text-[11px] text-slate-500 italic">
            Select one option from below
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {options.map((option) => {
            const optId = typeof option === 'object' ? option.id : option;
            const optText = typeof option === 'object' ? option.text : option;
            const isSelected = selectedOptionId === optId;

            return (
              <button
                key={optId}
                type="button"
                onClick={() => onSelectOption(optId, optText)}
                className={`p-4 rounded-2xl border text-left transition-all duration-200 flex items-start space-x-3.5 cursor-pointer ${
                  isSelected
                    ? 'bg-purple-950/40 border-purple-500 text-slate-100 shadow-lg shadow-purple-950/50 ring-1 ring-purple-500/50'
                    : 'bg-slate-950/70 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900/80'
                }`}
              >
                <div
                  className={`w-7 h-7 rounded-xl flex items-center justify-center font-bold text-xs shrink-0 transition-colors ${
                    isSelected
                      ? 'bg-purple-600 text-white shadow-md shadow-purple-600/40'
                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}
                >
                  {optId}
                </div>
                <div className="flex-1 pt-0.5">
                  <span className="text-sm font-mono font-medium block leading-snug break-words">
                    {optText}
                  </span>
                </div>
                {isSelected && (
                  <CheckCircle2 className="w-5 h-5 text-purple-400 shrink-0 mt-0.5 animate-in fade-in zoom-in duration-200" />
                )}
              </button>
            );
          })}
        </div>

        {/* Action Button Footer */}
        <div className="pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-slate-400">
            {selectedOptionId ? (
              <span className="text-purple-400 font-medium">
                Option <strong>{selectedOptionId}</strong> selected. Click Next Question to proceed.
              </span>
            ) : (
              <span className="text-amber-400/90 italic">
                Please select an option to submit your answer.
              </span>
            )}
          </p>

          <button
            type="button"
            onClick={onNextQuestion}
            disabled={savingAnswer || !selectedOptionId}
            className={`w-full sm:w-auto px-6 py-3 rounded-xl font-semibold text-sm transition-all duration-200 flex items-center justify-center space-x-2 ${
              selectedOptionId && !savingAnswer
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-600/30 active:scale-95'
                : 'bg-slate-800/70 text-slate-500 border border-slate-800 cursor-not-allowed'
            }`}
          >
            <span>{savingAnswer ? 'Saving Answer...' : isLastQuestion ? 'Complete Interview' : 'Next Question'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default PseudocodeMcqQuestion;
