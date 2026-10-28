import type { ChildProcess } from "node:child_process";
export const browserBudgets: Readonly<{
  startup: number;
  discovery: number;
  workflow: number;
  global: number;
  cleanup: number;
  shutdown: number;
}>;
export function resourceSnapshot(): object;
export type Diagnostics = {
  add(
    kind: string,
    value?: {
      code?: string;
      url?: string;
      status?: number;
      exitCode?: number;
      attempt?: number;
      signal?: string;
    },
  ): void;
  stage(value: string): void;
  snapshot(): { stage: string; truncated: boolean; events: object[] };
};
export function routeClass(url: string, base: string): string;
export function diagnostics(base: string): Diagnostics;
export function waitForDevTools(
  child: ChildProcess,
  diagnostic: Diagnostics,
  options?: {
    timeout?: number;
    timer?: typeof setTimeout;
    clear?: typeof clearTimeout;
    now?: () => number;
    evidence?: Record<string, number | boolean>;
  },
): Promise<{ port: number; browserSocket: string }>;
export function serverStatus(base: string): Promise<Record<string, number>>;
export const devtoolsFailures: Set<string>;
export function waitForPageTarget(
  child: ChildProcess,
  port: number,
  diagnostic: Diagnostics,
  options?: {
    deadline?: number;
    now?: () => number;
    request?: typeof fetch;
    timer?: typeof setTimeout;
    clear?: typeof clearTimeout;
    pause?: (ms: number, signal: AbortSignal) => Promise<void>;
  },
): Promise<{
  target: { id: string; webSocketDebuggerUrl: string };
  attempts: number;
}>;
