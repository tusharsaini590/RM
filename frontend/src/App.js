import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const KnowledgeCard = ({ content, onFeedback }) => {
  const [expanded, setExpanded] = useState(false);
  
  const handleExpand = () => {
    setExpanded(!expanded);
    if (!expanded) {
      onFeedback(content.id, 'expand');
    }
  };
  
  const handleFeedback = (action) => {
    onFeedback(content.id, action);
  };
  
  const getScoreColor = (score) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    return 'text-red-600';
  };
  
  const getUtilityBarWidth = (score) => {
    return Math.max(10, (score / 10) * 100);
  };
  
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 leading-tight mb-2">
            {content.title}
          </h3>
          <div className="flex items-center text-sm text-gray-600 space-x-4">
            <span className="font-medium">{content.source}</span>
            <span>{new Date(content.published_date).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
      
      {/* Cognitive Utility Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
          <span>Cognitive Utility Score</span>
          <span className="font-semibold">{content.cognitive_utility_score.toFixed(1)}/10</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${getUtilityBarWidth(content.cognitive_utility_score)}%` }}
          ></div>
        </div>
      </div>
      
      {/* Credibility Indicators */}
      <div className="grid grid-cols-3 gap-4 mb-4 p-3 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className={`text-sm font-semibold ${getScoreColor(content.knowledge_density_score)}`}>
            {content.knowledge_density_score.toFixed(1)}
          </div>
          <div className="text-xs text-gray-600">Knowledge</div>
        </div>
        <div className="text-center">
          <div className={`text-sm font-semibold ${getScoreColor(content.credibility_score)}`}>
            {content.credibility_score.toFixed(1)}
          </div>
          <div className="text-xs text-gray-600">Credibility</div>
        </div>
        <div className="text-center">
          <div className={`text-sm font-semibold ${getScoreColor(10 - content.distraction_score)}`}>
            {(10 - content.distraction_score).toFixed(1)}
          </div>
          <div className="text-xs text-gray-600">Focus</div>
        </div>
      </div>
      
      {/* Summary */}
      <div className="mb-4">
        <p className="text-gray-700 text-sm leading-relaxed">
          {content.summary || content.content.substring(0, 200) + '...'}
        </p>
      </div>
      
      {/* Tags */}
      {content.tags && content.tags.length > 0 && (
        <div className="mb-4">
          <div className="flex flex-wrap gap-2">
            {content.tags.slice(0, 5).map((tag, index) => (
              <span 
                key={index}
                className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Expandable Content */}
      {expanded && (
        <div className="border-t border-gray-200 pt-4 mb-4">
          <div className="text-gray-800 text-sm leading-relaxed whitespace-pre-wrap">
            {content.content}
          </div>
          
          {/* Evidence Links */}
          {content.evidence_links && content.evidence_links.length > 0 && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <h4 className="text-sm font-semibold text-blue-900 mb-2">Evidence & Sources</h4>
              <div className="space-y-1">
                {content.evidence_links.map((link, index) => (
                  <a 
                    key={index}
                    href={link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 text-xs block truncate"
                  >
                    {link}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <button
          onClick={handleExpand}
          className="flex items-center space-x-1 text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
        >
          <svg className={`w-4 h-4 transform transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
          <span>{expanded ? 'Collapse' : 'Read More'}</span>
        </button>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={() => handleFeedback('helpful')}
            className="flex items-center space-x-1 text-green-600 hover:text-green-800 text-sm transition-colors"
            title="Mark as helpful"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
            </svg>
            <span className="text-xs">{content.helpful_votes}</span>
          </button>
          
          <button
            onClick={() => handleFeedback('unhelpful')}
            className="flex items-center space-x-1 text-gray-400 hover:text-red-600 text-sm transition-colors"
            title="Mark as not helpful"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v2a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10H5a2 2 0 00-2 2v6a2 2 0 002 2h2.5" />
            </svg>
            <span className="text-xs">{content.unhelpful_votes}</span>
          </button>
          
          {content.source_url && (
            <a
              href={content.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-blue-600 text-sm transition-colors"
              title="View original source"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

const ControlPanel = ({ controls, onControlChange }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      <div className="flex flex-wrap items-center gap-6">
        {/* Serendipity Toggle */}
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="serendipity"
            checked={controls.serendipity}
            onChange={(e) => onControlChange('serendipity', e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
          />
          <label htmlFor="serendipity" className="text-sm font-medium text-gray-700">
            Serendipity Mode
          </label>
          <span className="text-xs text-gray-500">(discover unexpected)</span>
        </div>
        
        {/* Diversity Toggle */}
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="diversity"
            checked={controls.diversity}
            onChange={(e) => onControlChange('diversity', e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
          />
          <label htmlFor="diversity" className="text-sm font-medium text-gray-700">
            Diversity Control
          </label>
          <span className="text-xs text-gray-500">(avoid echo chambers)</span>
        </div>
        
        {/* Minimum Score Slider */}
        <div className="flex items-center space-x-3">
          <label className="text-sm font-medium text-gray-700">Min Score:</label>
          <input
            type="range"
            min="0"
            max="10"
            step="0.5"
            value={controls.minScore}
            onChange={(e) => onControlChange('minScore', parseFloat(e.target.value))}
            className="w-24 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
          <span className="text-sm text-gray-600 min-w-8">{controls.minScore}</span>
        </div>
        
        {/* Refresh Button */}
        <button
          onClick={() => onControlChange('refresh', true)}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
        >
          Refresh Feed
        </button>
      </div>
    </div>
  );
};

const ManualUploadModal = ({ isOpen, onClose, onUpload }) => {
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    source: 'Manual Upload'
  });
  const [isUploading, setIsUploading] = useState(false);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.content.trim()) {
      alert('Please fill in both title and content');
      return;
    }
    
    setIsUploading(true);
    try {
      await onUpload(formData);
      setFormData({ title: '', content: '', source: 'Manual Upload' });
      onClose();
    } catch (error) {
      alert('Error uploading content: ' + error.message);
    } finally {
      setIsUploading(false);
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Add Content Manually</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Title</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter article title..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Source</label>
              <input
                type="text"
                value={formData.source}
                onChange={(e) => setFormData({...formData, source: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Content source..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Content</label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({...formData, content: e.target.value})}
                rows={12}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Paste your content here..."
              />
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isUploading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {isUploading ? 'Analyzing...' : 'Upload & Analyze'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

function App() {
  const [content, setContent] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [controls, setControls] = useState({
    serendipity: false,
    diversity: false,
    minScore: 0,
    refresh: false
  });
  
  const fetchContent = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/content`, {
        params: {
          limit: 20,
          min_score: controls.minScore,
          serendipity: controls.serendipity,
          diversity: controls.diversity
        }
      });
      setContent(response.data);
    } catch (error) {
      console.error('Error fetching content:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const setupDefaultSources = async () => {
    try {
      await axios.post(`${API}/setup/default-sources`);
      console.log('Default sources set up');
    } catch (error) {
      console.error('Error setting up default sources:', error);
    }
  };
  
  const handleFeedback = async (contentId, action) => {
    try {
      await axios.post(`${API}/feedback`, {
        content_id: contentId,
        action: action
      });
      
      // Update local state for immediate feedback
      setContent(prev => prev.map(item => {
        if (item.id === contentId) {
          const updated = {...item};
          if (action === 'helpful') updated.helpful_votes = (updated.helpful_votes || 0) + 1;
          if (action === 'unhelpful') updated.unhelpful_votes = (updated.unhelpful_votes || 0) + 1;
          if (action === 'expand') updated.expand_count = (updated.expand_count || 0) + 1;
          return updated;
        }
        return item;
      }));
    } catch (error) {
      console.error('Error logging feedback:', error);
    }
  };
  
  const handleControlChange = (key, value) => {
    if (key === 'refresh') {
      fetchContent();
    } else {
      setControls(prev => ({...prev, [key]: value}));
    }
  };
  
  const handleManualUpload = async (uploadData) => {
    try {
      await axios.post(`${API}/content/manual`, uploadData);
      fetchContent(); // Refresh the feed
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Upload failed');
    }
  };
  
  useEffect(() => {
    setupDefaultSources();
    fetchContent();
  }, []);
  
  useEffect(() => {
    if (controls.serendipity !== false || controls.diversity !== false || controls.minScore !== 0) {
      fetchContent();
    }
  }, [controls.serendipity, controls.diversity, controls.minScore]);
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Knowledge First</h1>
              <p className="text-gray-600 text-sm">Distraction-free knowledge aggregator</p>
            </div>
            <button
              onClick={() => setShowUploadModal(true)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
            >
              Add Content
            </button>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        {/* Control Panel */}
        <ControlPanel 
          controls={controls} 
          onControlChange={handleControlChange}
        />
        
        {/* Content Feed */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading knowledge feed...</span>
          </div>
        ) : content.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-500 mb-4">
              <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
              </svg>
              <p className="text-lg">No content available yet</p>
              <p className="text-sm">Add RSS sources or upload content manually to get started</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {content.map((item) => (
              <KnowledgeCard 
                key={item.id} 
                content={item} 
                onFeedback={handleFeedback}
              />
            ))}
          </div>
        )}
      </main>
      
      {/* Upload Modal */}
      <ManualUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUpload={handleManualUpload}
      />
    </div>
  );
}

export default App;