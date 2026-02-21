"use client";

import TopBar from "@/components/TopBar";
import WorldMap from "@/components/WorldMap";
import OperationsStack from "@/components/OperationsStack";
import RunStream from "@/components/RunStream";
import StatusBanner from "@/components/StatusBanner";

export default function Home() {
  return (
    <div className="flex h-screen flex-col">
      <TopBar />
      <StatusBanner />
      <main className="grid flex-1 grid-cols-1 overflow-auto lg:grid-cols-[minmax(0,1fr)_448px] lg:overflow-hidden">
        <WorldMap />
        <OperationsStack />
      </main>
      <RunStream />
    </div>
  );
}
