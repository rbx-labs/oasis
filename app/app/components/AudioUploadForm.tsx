"use client";

import React, { useState } from "react";

interface AudioUploadFormProps {
  speakers: any;
}

export default function AudioUploadForm({ speakers }: AudioUploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    content: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setMessage({ type: "error", content: "Please select a file." });
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append(
      "start_timestamp",
      Math.floor(Date.now() / 1000).toString()
    );

    setIsLoading(true);
    setMessage(null);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL_BASE}/api/v1/audio/upload`,
        {
          method: "POST",
          body: formData,
          headers: {
            "X-API-Key": "your-super-secret-api-key",
          },
        }
      );

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      setMessage({
        type: "success",
        content: "File uploaded successfully.",
      });
      setFile(null);
      // Reset file input
      const fileInput = document.getElementById(
        "audioFile"
      ) as HTMLInputElement;
      if (fileInput) fileInput.value = "";
    } catch (error) {
      setMessage({
        type: "error",
        content: "An error occurred during file upload.",
      });
      console.error("Error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mx-auto p-4">
      <div className="bg-white rounded-lg shadow-lg p-6">
        {/* Speaker Table */}
        <div className="mb-12">
          <h2 className="text-xl font-semibold mb-4">
            Registered Speakers List
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[200px]">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Context
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created At
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {speakers.map((speaker: any) => (
                  <tr key={speaker.id}>
                    <td className="px-6 py-4 whitespace-normal text-sm text-gray-900">
                      {speaker.profile_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {speaker.speaker_label}
                    </td>
                    <td className="px-6 py-4 whitespace-normal text-sm text-gray-900">
                      {speaker.context}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(speaker.created_at).getTime()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* File Upload Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="audioFile"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Select WAV or M4A File
            </label>
            <input
              id="audioFile"
              type="file"
              accept=".wav, .m4a"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {message && (
            <div
              className={`p-3 rounded-md ${
                message.type === "success"
                  ? "bg-green-100 text-green-700"
                  : "bg-red-100 text-red-700"
              }`}
            >
              {message.content}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !file}
            className="w-full bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Uploading...
              </div>
            ) : (
              "Upload"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
