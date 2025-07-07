import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Video, Download, Trash2, Search, Filter } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const MyVideos = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchVideos();
  }, [currentPage, statusFilter]);

  const fetchVideos = async () => {
    try {
      const params = new URLSearchParams({
        page: currentPage,
        limit: 12
      });
      
      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      
      if (searchTerm) {
        params.append('search', searchTerm);
      }

      const response = await axios.get(`/api/videos?${params}`);
      setVideos(response.data.videos || []);
      setTotalPages(response.data.total_pages || 1);
    } catch (error) {
      toast.error('Failed to load videos');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchVideos();
  };

  const handleDelete = async (videoId) => {
    if (!window.confirm('Are you sure you want to delete this video?')) {
      return;
    }

    try {
      await axios.delete(`/api/videos/${videoId}`);
      toast.success('Video deleted successfully');
      fetchVideos();
    } catch (error) {
      toast.error('Failed to delete video');
    }
  };

  const handleDownload = async (videoId, title) => {
    try {
      const response = await axios.get(`/api/videos/${videoId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${title}.mp4`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success('Download started!');
    } catch (error) {
      toast.error('Failed to download video');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Videos</h1>
          <p className="text-gray-600">Manage and download your generated videos</p>
        </div>
        <Link
          to="/generate"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Video className="h-4 w-4 mr-2" />
          Create New Video
        </Link>
      </div>

      {/* Search and Filter */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="flex flex-col md:flex-row gap-4">
          <form onSubmit={handleSearch} className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search videos by title..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </form>
          
          <div className="flex items-center space-x-2">
            <Filter className="h-5 w-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Videos Grid */}
      {videos.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <Video className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No videos found</h3>
          <p className="text-gray-600 mb-6">
            {searchTerm || statusFilter !== 'all' 
              ? 'Try adjusting your search or filter criteria.'
              : 'You haven\'t created any videos yet.'
            }
          </p>
          <Link
            to="/generate"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <Video className="h-4 w-4 mr-2" />
            Create Your First Video
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {videos.map((video) => (
            <div key={video.id} className="bg-white rounded-lg shadow-md overflow-hidden">
              {/* Video Thumbnail */}
              <div className="aspect-video bg-gray-200 flex items-center justify-center">
                {video.status === 'completed' ? (
                  <video
                    className="w-full h-full object-cover"
                    src={video.output_path}
                    poster={video.thumbnail_path}
                  />
                ) : (
                  <Video className="h-12 w-12 text-gray-400" />
                )}
              </div>

              {/* Video Info */}
              <div className="p-4">
                <h3 className="font-semibold text-gray-900 mb-2 truncate">
                  {video.title}
                </h3>
                
                <div className="flex items-center justify-between mb-3">
                  <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(video.status)}`}>
                    {video.status}
                  </span>
                  <span className="text-sm text-gray-500">
                    {new Date(video.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>Duration:</span>
                    <span>{video.duration ? `${Math.round(video.duration)}s` : 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Size:</span>
                    <span>{video.file_size ? formatFileSize(video.file_size) : 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Resolution:</span>
                    <span>{video.resolution || 'N/A'}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-200">
                  {video.status === 'completed' && (
                    <button
                      onClick={() => handleDownload(video.id, video.title)}
                      className="flex items-center text-blue-600 hover:text-blue-700"
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Download
                    </button>
                  )}
                  
                  <button
                    onClick={() => handleDelete(video.id)}
                    className="flex items-center text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center mt-8">
          <nav className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <button
                key={page}
                onClick={() => setCurrentPage(page)}
                className={`px-3 py-2 border rounded-md text-sm font-medium ${
                  currentPage === page
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {page}
              </button>
            ))}
            
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </nav>
        </div>
      )}
    </div>
  );
};

export default MyVideos; 