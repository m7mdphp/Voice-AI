import React from 'react';
// Importing from the path requested by user: frontend/components/VoiceWidget.jsx
// Since we are in src/, we go up one level
import VoiceWidget from '../components/VoiceWidget';

function App() {
    // Example IDs for MVP
    const tenantId = "demo-tenant";
    const userId = "user-123";

    return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">
            <div className="text-center">
                <h1 className="text-3xl font-bold mb-8 text-gray-800">نظام ترياق الصوتي</h1>
                <VoiceWidget tenantId={tenantId} userId={userId} />
            </div>
        </div>
    );
}

export default App;
