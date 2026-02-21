import dynamic from "next/dynamic";

const StormOpsMap = dynamic(() => import("./components/StormOpsMap"), {
  ssr: false,
  loading: () => (
    <div
      style={{
        height: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#0f172a",
        color: "#94a3b8",
      }}
    >
      Loading map…
    </div>
  ),
});

export default function Home() {
  return (
    <main className="app">
      <StormOpsMap />
    </main>
  );
}
