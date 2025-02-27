import React from "react";
import AudioUploadForm from "./components/AudioUploadForm";

export const fetchCache = "force-no-store";

async function getSpeakers() {
  const res = await fetch(`${process.env.INTERNAL_URL_BASE}/api/v1/speaker`, {
    headers: {
      "X-API-Key": process.env.API_KEY,
    },
  });
  if (!res.ok) throw new Error("Failed to fetch speakers");
  return await res.json();
}

export default async function Home() {
  const speakers = await getSpeakers();
  return (
    <main>
      <AudioUploadForm speakers={speakers} />
    </main>
  );
}
