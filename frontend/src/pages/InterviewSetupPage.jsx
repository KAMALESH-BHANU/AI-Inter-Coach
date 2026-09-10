import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { resumeAPI, interviewAPI } from '../services/api';
import SkillSelector from '../components/SkillSelector';
import { FileUp, ListChecks, PlayCircle, AlertCircle, CheckCircle2, FolderGit2, X, Plus, Sparkles } from 'lucide-react';

const InterviewSetupPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('manual'); // 'manual' or 'resume'

  // Resume state
  const [selectedFile, setSelectedFile] = useState(null);
  const [parsing, setParsing] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [parseError, setParseError] = useState('');

  // Manual skills state
  const [manualSkills, setManualSkills] = useState(['Java', 'Python', 'React', 'MySQL', 'System Design']);

  // Loading state
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState('');

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setSelectedFile(file);
    setParseError('');
    setParsing(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await resumeAPI.upload(formData);
      setExtractedData(res.data);
    } catch (err) {
      setParseError(err.response?.data?.detail || 'Failed to parse resume document.');
    } finally {
      setParsing(false);
    }
  };

  // Remove skill from extracted resume skills
  const removeResumeSkill = (skillToRemove) => {
    if (!extractedData) return;
    setExtractedData({
      ...extractedData,
      skills: extractedData.skills.filter((s) => s !== skillToRemove)
    });
  };

  // Add/update skills in resume flow
  const updateResumeSkills = (newSkillsList) => {
    if (!extractedData) return;
    setExtractedData({
      ...extractedData,
      skills: newSkillsList
    });
  };

  const handleStartInterview = async () => {
    setStartError('');
    setStarting(true);

    let finalSkills = [];
    let finalProjects = [];

    if (activeTab === 'resume' && extractedData) {
      finalSkills = extractedData.skills;
      finalProjects = extractedData.projects || [];
    } else {
      finalSkills = manualSkills;
      finalProjects = [];
    }

    if (!finalSkills || finalSkills.length === 0) {
      setStartError('Please select or extract at least 1 technical skill to start the interview.');
      setStarting(false);
      return;
    }

    try {
      const res = await interviewAPI.create({
        skills: finalSkills,
        projects: finalProjects
      });
      const sessionId = res.data.session_id;
      navigate(`/interview/${sessionId}`);
    } catch (err) {
      setStartError(err.response?.data?.detail || 'Failed to start interview session.');
    } finally {
      setStarting(false);
    }
  };

  const effectiveSkillsCount = activeTab === 'resume' 
    ? (extractedData?.skills?.length || 0) 
    : manualSkills.length;

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-extrabold text-slate-100">Configure Your Mock Interview</h1>
        <p className="text-slate-400 text-sm max-w-xl mx-auto">
          Choose how you want to prepare: select skills manually from the taxonomy or upload your resume for automatic parsing.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex rounded-2xl bg-slate-900/90 p-1.5 border border-slate-800 max-w-md mx-auto shadow-lg">
        <button
          type="button"
          onClick={() => setActiveTab('manual')}
          className={`flex-1 py-3 text-xs font-bold rounded-xl transition-all flex items-center justify-center space-x-2 ${
            activeTab === 'manual'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <ListChecks className="w-4 h-4" />
          <span>Select Skills Manually</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('resume')}
          className={`flex-1 py-3 text-xs font-bold rounded-xl transition-all flex items-center justify-center space-x-2 ${
            activeTab === 'resume'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileUp className="w-4 h-4" />
          <span>Upload Resume</span>
        </button>
      </div>

      {/* Tab Content */}
      <div className="glass-card p-8 rounded-3xl border border-slate-800 space-y-6 shadow-2xl">
        {activeTab === 'manual' ? (
          /* Method B: Manual Skill Selection */
          <div className="space-y-4">
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <span>Select Your Technical Skills</span>
                <Sparkles className="w-4 h-4 text-blue-400" />
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Choose the programming languages, frameworks, databases, and core CS subjects you want the 10 questions generated on.
              </p>
            </div>
            <SkillSelector selectedSkills={manualSkills} onChange={setManualSkills} />
          </div>
        ) : (
          /* Method A: Resume Upload */
          <div className="space-y-6">
            <div className="border-2 border-dashed border-slate-700 hover:border-blue-500/60 rounded-2xl p-8 text-center space-y-4 transition-colors bg-slate-950/30">
              <FileUp className="w-12 h-12 text-blue-400 mx-auto" />
              <div>
                <h3 className="text-base font-bold text-slate-200">Upload Resume Document</h3>
                <p className="text-xs text-slate-400 mt-1">Supported formats: PDF, DOCX, TXT (Max size: 10MB)</p>
              </div>
              <label className="inline-block cursor-pointer px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl transition-colors shadow-md shadow-blue-500/20">
                <span>Browse Resume File</span>
                <input
                  type="file"
                  accept=".pdf,.docx,.doc,.txt"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
              {selectedFile && (
                <p className="text-xs text-emerald-400 font-medium">Selected: {selectedFile.name}</p>
              )}
            </div>

            {parsing && (
              <div className="text-center text-sm text-slate-400 py-4 flex items-center justify-center space-x-2">
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                <span>Extracting technical skills and projects...</span>
              </div>
            )}

            {parseError && (
              <div className="flex items-center space-x-2 bg-rose-500/10 border border-rose-500/30 p-3.5 rounded-xl text-rose-300 text-xs font-medium">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{parseError}</span>
              </div>
            )}

            {extractedData && (
              <div className="space-y-5 bg-slate-900/60 p-6 rounded-2xl border border-slate-800">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-emerald-400 font-bold text-sm">
                    <CheckCircle2 className="w-5 h-5" />
                    <span>Resume Processed Successfully</span>
                  </div>
                  <span className="text-xs text-slate-400">
                    {extractedData.skills.length} skills identified
                  </span>
                </div>

                {/* Identified Projects */}
                {extractedData.projects && extractedData.projects.length > 0 && (
                  <div className="space-y-2 border-b border-slate-800 pb-4">
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Identified Projects ({extractedData.projects.length})</h4>
                    <div className="space-y-2">
                      {extractedData.projects.map((proj, idx) => (
                        <div key={idx} className="flex items-center space-x-2.5 p-2.5 bg-slate-950/60 rounded-xl border border-slate-800 text-xs text-slate-200">
                          <FolderGit2 className="w-4 h-4 text-blue-400 flex-shrink-0" />
                          <span className="font-bold text-slate-100">{proj.name}</span>
                          <span className="text-slate-400">({proj.technologies.join(', ')})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Extracted Skills & Customizer */}
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Confirmed Skills for Interview (Add or Remove)
                  </h4>
                  <SkillSelector
                    selectedSkills={extractedData.skills}
                    onChange={updateResumeSkills}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {startError && (
          <div className="flex items-center space-x-2 bg-rose-500/10 border border-rose-500/30 p-3.5 rounded-xl text-rose-300 text-xs font-medium">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{startError}</span>
          </div>
        )}

        {/* Start Interview Footer */}
        <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
          <div className="text-xs text-slate-400">
            Interview includes: <strong className="text-slate-200">3 Project + 5 Technical + 2 Pseudocode = 10 Questions</strong>
          </div>

          <button
            type="button"
            onClick={handleStartInterview}
            disabled={starting || effectiveSkillsCount === 0}
            className="px-8 py-3.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl transition-all shadow-xl shadow-blue-500/25 flex items-center space-x-2.5 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <PlayCircle className="w-5 h-5" />
            <span>{starting ? 'Generating Questions...' : 'Start 10-Question Interview'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default InterviewSetupPage;
