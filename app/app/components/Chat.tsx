"use client";

import React, { useState } from "react";

interface ChatProps {
  speakers: any;
}

export default function Chat({ speakers }: ChatProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    content: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setMessage({ type: "error", content: "파일을 선택해주세요." });
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
      const response = await fetch("/api/v1/audio/upload", {
        method: "POST",
        body: formData,
        headers: {
          "X-API-Key": "your-super-secret-api-key",
        },
      });

      if (!response.ok) {
        throw new Error("업로드 실패");
      }

      setMessage({
        type: "success",
        content: "파일이 성공적으로 업로드되었습니다.",
      });
      setFile(null);
      // 파일 input 초기화
      const fileInput = document.getElementById(
        "audioFile"
      ) as HTMLInputElement;
      if (fileInput) fileInput.value = "";
    } catch (error) {
      setMessage({
        type: "error",
        content: "파일 업로드 중 오류가 발생했습니다.",
      });
      console.error("Error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div className="bg-white rounded-lg shadow-lg p-6">
        {/* 스피커 테이블 */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4">등록된 화자 목록</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    이름
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    컨텍스트
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    생성일
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
                      {new Date(speaker.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 파일 업로드 폼 */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="audioFile"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              WAV 파일 선택
            </label>
            <input
              id="audioFile"
              type="file"
              accept=".wav"
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
                업로드 중...
              </div>
            ) : (
              "업로드"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
