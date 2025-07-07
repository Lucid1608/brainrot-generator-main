import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Play, Video, Zap, Users } from 'lucide-react';

const Home = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Transform Your Stories Into
            <span className="text-blue-600"> Viral Videos</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Create engaging TikTok-style videos from any text story. Our AI-powered platform 
            generates professional videos with voice-over, background music, and stunning visuals.
          </p>
          
          {user ? (
            <Link
              to="/generate"
              className="inline-flex items-center px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Play className="mr-2" size={24} />
              Start Creating
            </Link>
          ) : (
            <div className="space-x-4">
              <Link
                to="/register"
                className="inline-flex items-center px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition-colors"
              >
                Get Started Free
              </Link>
              <Link
                to="/login"
                className="inline-flex items-center px-8 py-4 bg-white text-blue-600 text-lg font-semibold rounded-lg border-2 border-blue-600 hover:bg-blue-50 transition-colors"
              >
                Sign In
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Why Choose Brainrot Generator?
          </h2>
          <p className="text-xl text-gray-600">
            Everything you need to create viral content in minutes
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-white p-8 rounded-lg shadow-lg">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <Zap className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">
              Lightning Fast
            </h3>
            <p className="text-gray-600">
              Generate professional videos in under 2 minutes. No complex editing software required.
            </p>
          </div>

          <div className="bg-white p-8 rounded-lg shadow-lg">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <Video className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">
              AI-Powered
            </h3>
            <p className="text-gray-600">
              Advanced AI technology creates natural-sounding voice-overs and engaging visuals.
            </p>
          </div>

          <div className="bg-white p-8 rounded-lg shadow-lg">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <Users className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">
              User-Friendly
            </h3>
            <p className="text-gray-600">
              Simple interface designed for creators of all skill levels. No technical knowledge needed.
            </p>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            How It Works
          </h2>
          <p className="text-xl text-gray-600">
            Three simple steps to create your viral video
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
              1
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">
              Write Your Story
            </h3>
            <p className="text-gray-600">
              Enter your story or script. Our AI will convert it into natural-sounding speech.
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
              2
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">
              Choose Your Style
            </h3>
            <p className="text-gray-600">
              Select from multiple voices and background styles to match your content.
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
              3
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">
              Download & Share
            </h3>
            <p className="text-gray-600">
              Get your video instantly and share it on TikTok, Instagram, or any platform.
            </p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="bg-blue-600 rounded-2xl p-12 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Create Your First Video?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of creators who are already making viral content
          </p>
          {user ? (
            <Link
              to="/generate"
              className="inline-flex items-center px-8 py-4 bg-white text-blue-600 text-lg font-semibold rounded-lg hover:bg-gray-100 transition-colors"
            >
              <Play className="mr-2" size={24} />
              Start Creating Now
            </Link>
          ) : (
            <Link
              to="/register"
              className="inline-flex items-center px-8 py-4 bg-white text-blue-600 text-lg font-semibold rounded-lg hover:bg-gray-100 transition-colors"
            >
              Get Started Free
            </Link>
          )}
        </div>
      </div>
    </div>
  );
};

export default Home; 