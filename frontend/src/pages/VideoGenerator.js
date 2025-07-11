import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Play, Download, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';

const VideoGenerator = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
    story: '',
    voice: 'emily',
    background: 'default'
  });
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedVideo, setGeneratedVideo] = useState(null);

  const voiceOptions = [
    { id: 'emily', name: 'Emily' }
  ];

  const backgroundOptions = [
    { id: 'default', name: 'Default Background' },
    { id: 'nature', name: 'Nature' },
    { id: 'city', name: 'City' },
    { id: 'abstract', name: 'Abstract' }
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title.trim() || !formData.story.trim()) {
      toast.error('Please fill in all required fields');
      return;
    }

    setIsGenerating(true);
    
    try {
      const response = await axios.post('/api/generate', formData);
      
      if (response.data.success) {
        setGeneratedVideo(response.data.video);
        toast.success('Video generated successfully!');
      } else {
        toast.error(response.data.message || 'Failed to generate video');
      }
    } catch (error) {
      toast.error(error.response?.data?.message || 'An error occurred');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = async () => {
    if (!generatedVideo) return;
    
    try {
      const response = await axios.get(`/api/videos/${generatedVideo.id}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${generatedVideo.title}.mp4`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success('Download started!');
    } catch (error) {
      toast.error('Failed to download video');
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Generate Your Video</h1>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Title Input */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
              Video Title *
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter a catchy title for your video"
              required
            />
          </div>

          {/* Story Input */}
          <div>
            <label htmlFor="story" className="block text-sm font-medium text-gray-700 mb-2">
              Story Content *
            </label>
            <textarea
              id="story"
              name="story"
              value={formData.story}
              onChange={handleInputChange}
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Write your story here. This will be converted to speech and used in your video."
              required
            />
            <p className="text-sm text-gray-500 mt-1">
              {formData.story.length} characters
            </p>
          </div>

          {/* Voice Selection */}
          <div>
            <label htmlFor="voice" className="block text-sm font-medium text-gray-700 mb-2">
              Voice Selection
            </label>
            <select
              id="voice"
              name="voice"
              value={formData.voice}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {voiceOptions.map(voice => (
                <option key={voice.id} value={voice.id}>
                  {voice.name}
                </option>
              ))}
            </select>
          </div>

          {/* Background Selection */}
          <div>
            <label htmlFor="background" className="block text-sm font-medium text-gray-700 mb-2">
              Background Style
            </label>
            <select
              id="background"
              name="background"
              value={formData.background}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {backgroundOptions.map(bg => (
                <option key={bg.id} value={bg.id}>
                  {bg.name}
                </option>
              ))}
            </select>
          </div>

          {/* Generate Button */}
          <button
            type="submit"
            disabled={isGenerating}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isGenerating ? (
              <>
                <Loader2 className="animate-spin mr-2" size={20} />
                Generating Video...
              </>
            ) : (
              <>
                <Play className="mr-2" size={20} />
                Generate Video
              </>
            )}
          </button>
        </form>

        {/* Generated Video Display */}
        {generatedVideo && (
          <div className="mt-8 p-6 bg-gray-50 rounded-lg">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Generated Video</h2>
            
            <div className="aspect-video bg-black rounded-lg mb-4">
              <video
                controls
                className="w-full h-full rounded-lg"
                src={generatedVideo.url}
              >
                Your browser does not support the video tag.
              </video>
            </div>
            
            <div className="flex gap-4">
              <button
                onClick={handleDownload}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                <Download className="mr-2" size={16} />
                Download
              </button>
              
              <button
                onClick={() => navigate('/videos')}
                className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                View All Videos
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoGenerator; 