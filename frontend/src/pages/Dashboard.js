import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Play, Video, Download, Clock, TrendingUp } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalVideos: 0,
    videosThisMonth: 0,
    planLimit: 0,
    planUsed: 0
  });
  const [recentVideos, setRecentVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsResponse, videosResponse] = await Promise.all([
        axios.get('/api/user/stats'),
        axios.get('/api/videos?limit=5')
      ]);

      setStats(statsResponse.data);
      setRecentVideos(videosResponse.data.videos || []);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getPlanProgress = () => {
    if (stats.planLimit === 0) return 0;
    return Math.min((stats.planUsed / stats.planLimit) * 100, 100);
  };

  const getPlanName = () => {
    if (stats.planLimit >= 500) return 'Business';
    if (stats.planLimit >= 50) return 'Pro';
    return 'Free';
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
      {/* Welcome Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome back, {user?.username || user?.email}!
        </h1>
        <p className="text-gray-600">
          Ready to create your next viral video? Let's get started.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Video className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Videos</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalVideos}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">This Month</p>
              <p className="text-2xl font-bold text-gray-900">{stats.videosThisMonth}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Clock className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Plan</p>
              <p className="text-2xl font-bold text-gray-900">{getPlanName()}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Download className="h-6 w-6 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Usage</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats.planUsed}/{stats.planLimit}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Plan Progress */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Plan Usage</h2>
        <div className="mb-2 flex justify-between text-sm text-gray-600">
          <span>{getPlanName()} Plan</span>
          <span>{stats.planUsed} / {stats.planLimit} videos</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${getPlanProgress()}%` }}
          ></div>
        </div>
        {getPlanProgress() >= 80 && (
          <p className="text-sm text-orange-600 mt-2">
            You're approaching your plan limit. Consider upgrading for more videos.
          </p>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link
            to="/generate"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
          >
            <Play className="h-8 w-8 text-blue-600 mr-4" />
            <div>
              <h3 className="font-semibold text-gray-900">Create New Video</h3>
              <p className="text-sm text-gray-600">Generate a new video from your story</p>
            </div>
          </Link>

          <Link
            to="/videos"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
          >
            <Video className="h-8 w-8 text-blue-600 mr-4" />
            <div>
              <h3 className="font-semibold text-gray-900">View My Videos</h3>
              <p className="text-sm text-gray-600">Browse and manage your videos</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Videos */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Recent Videos</h2>
          <Link
            to="/videos"
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            View all
          </Link>
        </div>

        {recentVideos.length === 0 ? (
          <div className="text-center py-8">
            <Video className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No videos yet. Create your first video!</p>
            <Link
              to="/generate"
              className="inline-flex items-center mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <Play className="h-4 w-4 mr-2" />
              Create Video
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {recentVideos.map((video) => (
              <div
                key={video.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
              >
                <div className="flex items-center">
                  <div className="w-16 h-12 bg-gray-200 rounded flex items-center justify-center mr-4">
                    <Video className="h-6 w-6 text-gray-400" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{video.title}</h3>
                    <p className="text-sm text-gray-600">
                      {new Date(video.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    video.status === 'completed' ? 'bg-green-100 text-green-800' :
                    video.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {video.status}
                  </span>
                  {video.status === 'completed' && (
                    <button
                      onClick={() => window.open(`/api/videos/${video.id}/download`, '_blank')}
                      className="p-2 text-gray-400 hover:text-blue-600"
                    >
                      <Download className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard; 