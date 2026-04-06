'use client';

import { useState } from 'react';
import { VoiceChat } from '../components/VoiceChat';

export default function TestVoicePage() {
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [language, setLanguage] = useState<'en-IN' | 'hi-IN'>('en-IN');

  const handleTranscript = (text: string) => {
    setTranscript(text);
    // Simulate a response
    setResponse(`You said: "${text}". This is a test response that will be read aloud.`);
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Voice Feature Test Page</h1>
        
        {/* Language Selector */}
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <h2 className="font-semibold mb-3">Select Language:</h2>
          <div className="flex gap-3">
            <button
              onClick={() => setLanguage('en-IN')}
              className={`px-4 py-2 rounded ${
                language === 'en-IN' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-slate-100 text-slate-700'
              }`}
            >
              English (India)
            </button>
            <button
              onClick={() => setLanguage('hi-IN')}
              className={`px-4 py-2 rounded ${
                language === 'hi-IN' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-slate-100 text-slate-700'
              }`}
            >
              हिन्दी (Hindi)
            </button>
          </div>
        </div>

        {/* Voice Controls */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="font-semibold mb-4">Voice Controls:</h2>
          <VoiceChat 
            onTranscript={handleTranscript}
            lastResponse={response}
            language={language}
          />
        </div>

        {/* Results Display */}
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="font-semibold text-sm text-slate-600 mb-2">Your Input (Speech-to-Text):</h3>
            <p className="text-lg">{transcript || 'Click the microphone and speak...'}</p>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="font-semibold text-sm text-slate-600 mb-2">System Response (Will be read aloud):</h3>
            <p className="text-lg">{response || 'Waiting for input...'}</p>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-6 bg-blue-50 border border-blue-200 p-4 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">How to Test:</h3>
          <ol className="list-decimal list-inside space-y-1 text-sm text-blue-800">
            <li>Click the microphone button 🎤</li>
            <li>Speak your question (in English or Hindi)</li>
            <li>See the transcript appear above</li>
            <li>Click the speaker button 🔊 to hear the response</li>
            <li>Try switching languages and repeat</li>
          </ol>
        </div>
      </div>
    </div>
  );
}