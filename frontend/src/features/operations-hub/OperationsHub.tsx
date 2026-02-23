import { useState } from "react";
import { ProcessList } from "./ProcessList";
import { ControlPanel } from "./ControlPanel";

export function OperationsHub({ token }: { token: string | null }): JSX.Element {
  const [selectedProcessId, setSelectedProcessId] = useState<string | undefined>();

  return (
    <div className="operations-hub-container">
      <ProcessList token={token} onSelectProcess={setSelectedProcessId} selectedProcessId={selectedProcessId} />
      <ControlPanel token={token} processId={selectedProcessId} />
    </div>
  );
}
