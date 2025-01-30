"use client";

import React from "react";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">
          Oasis Audio Processing
        </h1>
        <div className="bg-white rounded-lg shadow-lg p-6">
          <p className="text-lg text-gray-700">
            Welcome to the Oasis audio processing platform. Upload your audio
            files and manage transcriptions here.
          </p>
        </div>
      </div>
    </main>
  );
}
