// Configure the page to render dynamically
export const dynamic = "force-dynamic";

async function getAudios() {
  const res = await fetch("http://localhost:8000/v1/audio/all", {
    headers: {
      "X-API-Key": "your-super-secret-api-key",
    },
  });
  if (!res.ok) throw new Error("Failed to fetch audios");
  return res.json();
}

export default async function AudiosPage() {
  const audios = await getAudios();

  return (
    <div className="max-w-2xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Audio Files</h1>
      <div className="space-y-4">
        {audios.map((audio) => (
          <div key={audio.id} className="bg-white p-4 rounded-lg shadow">
            <h2 className="font-semibold">{audio.filename}</h2>
            <p className="text-sm text-gray-500">
              Created: {new Date(audio.created_at).toLocaleString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
