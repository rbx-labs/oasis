"use client";

import React, { useState, useEffect } from "react";

export default function Chat() {
  const [speakersList, setSpeakersList] = useState([]);

  useEffect(() => {
    const fetchSpeakers = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_INTERNAL_URL_BASE}/api/v1/speaker`,
          {
            headers: {
              "X-API-Key": process.env.NEXT_PUBLIC_API_KEY,
            },
          }
        );
        if (!response.ok) throw new Error("Failed to fetch speakers");
        const data = await response.json();
        setSpeakersList(data);
      } catch (error) {
        console.error("Error fetching speakers:", error);
      }
    };

    fetchSpeakers();
  }, []);

  const handleDeleteSpeaker = async (speakerId: string) => {
    if (!window.confirm("Are you sure you want to delete this speaker?")) {
      return;
    }
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_INTERNAL_URL_BASE}/api/v1/speaker/${speakerId}`,
        {
          method: "DELETE",
          headers: {
            "X-API-Key": process.env.NEXT_PUBLIC_API_KEY,
          },
        }
      );
      if (!response.ok) throw new Error("Failed to delete speaker");
      setSpeakersList(speakersList.filter((s) => s.id !== speakerId));
    } catch (error) {
      console.error("Error deleting speaker:", error);
    }
  };

  const handleResetSpeakers = async () => {
    if (!window.confirm("Are you sure you want to reset all speakers?")) {
      return;
    }
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_INTERNAL_URL_BASE}/api/v1/speaker/reset`,
        {
          method: "POST",
          headers: {
            "X-API-Key": process.env.NEXT_PUBLIC_API_KEY,
          },
        }
      );
      if (!response.ok) throw new Error("Failed to reset speakers");
      setSpeakersList([]);
    } catch (error) {
      console.error("Error resetting speakers:", error);
    }
  };

  return (
    <div className="mx-auto p-4">
      <div className="bg-white rounded-lg shadow-lg p-6">
        {/* 스피커 테이블 */}
        <div className="mb-12">
          <h2 className="text-xl font-semibold mb-4">등록된 화자 목록</h2>
          <button
            onClick={handleResetSpeakers}
            className="mb-4 bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600"
          >
            Reset Speakers
          </button>
          <div className="overflow-x-auto">
            <table className="w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[200px]">
                    이름
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    컨텍스트
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    생성일
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {speakersList.map((speaker: any) => (
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <button
                        onClick={() => handleDeleteSpeaker(speaker.id)}
                        className="bg-red-500 text-white px-2 py-1 rounded-lg hover:bg-red-600"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
