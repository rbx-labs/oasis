import { Speaker } from "../types/speaker";

interface SpeakerTableProps {
  speakers: Speaker[];
}

export default function SpeakerTable({ speakers }: SpeakerTableProps) {
  return (
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
                생성일
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {speakers.map((speaker) => (
              <tr key={speaker.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {speaker.id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {speaker.name}
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
  );
}
