"use client";

import React from "react";
import Chat from "./components/Chat";

export default function Home() {
  return (
    <main>
      <Chat />
      <img src="/images/homepage.png" alt="Homepage" className="mx-auto" />
    </main>
  );
}
