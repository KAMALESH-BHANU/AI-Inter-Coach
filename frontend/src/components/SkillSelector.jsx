import React, { useState, useEffect, useRef } from 'react';
import { questionAPI } from '../services/api';
import { Search, Check, X, Code, CheckCircle2, ChevronDown, ChevronUp, Layers, Tag } from 'lucide-react';

const SkillSelector = ({ selectedSkills = [], onChange }) => {
  const [categories, setCategories] = useState({});
  const [flatSkills, setFlatSkills] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [activeCategory, setActiveCategory] = useState(null);

  const containerRef = useRef(null);

  // Fetch skill taxonomy from centralized backend API
  useEffect(() => {
    const loadSkillData = async () => {
      try {
        const [catRes, flatRes] = await Promise.all([
          questionAPI.getCategories(),
          questionAPI.getSkills('')
        ]);
        setCategories(catRes.data || {});
        setFlatSkills(flatRes.data || []);
      } catch (err) {
        console.error('Failed to fetch centralized skill taxonomy:', err);
      }
    };
    loadSkillData();
  }, []);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Toggle skill selection with duplicate prevention
  const toggleSkill = (skill) => {
    if (selectedSkills.includes(skill)) {
      onChange(selectedSkills.filter((s) => s !== skill));
    } else {
      onChange([...new Set([...selectedSkills, skill])]);
    }
  };

  // Remove individual skill
  const removeSkill = (skill) => {
    onChange(selectedSkills.filter((s) => s !== skill));
  };

  // Filter skills based on search term
  const query = searchTerm.toLowerCase().trim();
  const searchResults = query
    ? flatSkills.filter((s) => s.toLowerCase().includes(query))
    : [];

  return (
    <div ref={containerRef} className="space-y-4 relative">
      {/* 1. Selected Skills Badge Container */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
            <Tag className="w-3.5 h-3.5 text-blue-400" />
            <span>Confirmed Technical Skills ({selectedSkills.length})</span>
          </label>
          {selectedSkills.length > 0 && (
            <button
              type="button"
              onClick={() => onChange([])}
              className="text-xs text-rose-400 hover:text-rose-300 font-medium transition-colors"
            >
              Clear All
            </button>
          )}
        </div>

        <div className="flex flex-wrap gap-2 min-h-[52px] p-3 bg-slate-900/90 rounded-2xl border border-slate-800 items-center">
          {selectedSkills.length === 0 ? (
            <span className="text-slate-500 text-xs italic px-1">
              No skills selected yet. Search or browse categories below to add skills for your interview.
            </span>
          ) : (
            selectedSkills.map((skill) => (
              <span
                key={skill}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-blue-600/20 border border-blue-500/40 text-blue-300 rounded-xl text-xs font-semibold shadow-sm transition-all animate-fadeIn"
              >
                <span>{skill}</span>
                <button
                  type="button"
                  onClick={() => removeSkill(skill)}
                  className="p-0.5 hover:bg-blue-500/30 rounded-md text-blue-400 hover:text-blue-100 transition-colors"
                  aria-label={`Remove ${skill}`}
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </span>
            ))
          )}
        </div>
      </div>

      {/* 2. Search & Browse Dropdown Trigger */}
      <div className="relative">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-4 top-3.5" />
          <input
            type="text"
            placeholder="Search skills (e.g. Java, React, Python, Spring Boot, MySQL, Docker, AWS)..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              if (!isOpen) setIsOpen(true);
            }}
            onFocus={() => setIsOpen(true)}
            className="w-full bg-slate-900 border border-slate-800 text-slate-100 pl-11 pr-10 py-3 rounded-2xl text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-inner placeholder-slate-500"
          />
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="absolute right-3.5 top-3.5 text-slate-400 hover:text-slate-200"
          >
            {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>

        {/* 3. Dropdown Menu */}
        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-slate-900/95 backdrop-blur-xl border border-slate-700/80 rounded-2xl shadow-2xl z-40 p-3 space-y-3 max-h-[380px] overflow-hidden flex flex-col animate-in fade-in slide-in-from-top-2 duration-150">
            
            {/* Search Results Mode */}
            {query ? (
              <div className="flex-1 overflow-y-auto pr-1 space-y-1">
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-2 py-1">
                  Search Results ({searchResults.length})
                </p>
                {searchResults.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-500">
                    No matching skills found in taxonomy for "{searchTerm}"
                  </div>
                ) : (
                  searchResults.map((skill) => {
                    const isSelected = selectedSkills.includes(skill);
                    return (
                      <button
                        key={skill}
                        type="button"
                        onClick={() => toggleSkill(skill)}
                        className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all text-left ${
                          isSelected
                            ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                            : 'text-slate-300 hover:bg-slate-800'
                        }`}
                      >
                        <div className="flex items-center space-x-2.5">
                          <Code className={`w-3.5 h-3.5 ${isSelected ? 'text-white' : 'text-blue-400'}`} />
                          <span>{skill}</span>
                        </div>
                        {isSelected && <Check className="w-4 h-4 text-white" />}
                      </button>
                    );
                  })
                )}
              </div>
            ) : (
              /* Categorized Tree Mode */
              <div className="flex-1 overflow-y-auto pr-1 space-y-2">
                {Object.entries(categories).map(([catName, skills]) => {
                  const isExpanded = activeCategory === catName;
                  const selectedInCat = skills.filter((s) => selectedSkills.includes(s)).length;

                  return (
                    <div key={catName} className="rounded-xl border border-slate-800/80 bg-slate-950/40 overflow-hidden">
                      <button
                        type="button"
                        onClick={() => setActiveCategory(isExpanded ? null : catName)}
                        className="w-full flex items-center justify-between p-3 text-xs font-bold text-slate-200 hover:bg-slate-800/50 transition-colors text-left"
                      >
                        <div className="flex items-center space-x-2">
                          <Layers className="w-3.5 h-3.5 text-blue-400" />
                          <span>{catName}</span>
                          {selectedInCat > 0 && (
                            <span className="px-2 py-0.5 bg-blue-600/30 text-blue-300 rounded-full text-[10px] font-extrabold border border-blue-500/30">
                              {selectedInCat}
                            </span>
                          )}
                        </div>
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />}
                      </button>

                      {isExpanded && (
                        <div className="p-2.5 pt-0 grid grid-cols-1 sm:grid-cols-2 gap-1.5 border-t border-slate-800/60 bg-slate-900/30">
                          {skills.map((skill) => {
                            const isSelected = selectedSkills.includes(skill);
                            return (
                              <button
                                key={skill}
                                type="button"
                                onClick={() => toggleSkill(skill)}
                                className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs transition-all text-left ${
                                  isSelected
                                    ? 'bg-blue-600 text-white font-semibold shadow-sm'
                                    : 'text-slate-300 hover:bg-slate-800'
                                }`}
                              >
                                <span>{skill}</span>
                                {isSelected && <Check className="w-3.5 h-3.5 text-white" />}
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* 4. Dropdown Footer with Done Button */}
            <div className="pt-2.5 border-t border-slate-800 flex justify-between items-center px-1">
              <span className="text-xs text-slate-400 font-medium">
                <strong className="text-blue-400">{selectedSkills.length}</strong> skills selected
              </span>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl flex items-center space-x-1.5 transition-all shadow-md shadow-blue-500/25"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Done</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SkillSelector;
