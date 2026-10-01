import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api";
import { useUI } from "@/store";

/** One generation, polled every 500 ms while a job runs (Phase 5A swaps this for SSE). */
export function useGen(id: number | null) {
  return useQuery({
    queryKey: ["gen", id],
    queryFn: () => api.generation(id as number),
    enabled: id !== null,
    refetchInterval: (q) => (q.state.data?.busy ? 500 : 2000),
  });
}

export function useGenList() {
  return useQuery({ queryKey: ["gens"], queryFn: api.generations, refetchInterval: 2000 });
}

/** A server action: errors (the 409 reasons) are shown inline in the notice bar, success refreshes every query. */
export function useAct<A extends unknown[], R>(fn: (...a: A) => Promise<R>, ok?: string | ((r: R) => string | void)) {
  const qc = useQueryClient();
  const say = useUI((s) => s.say);
  return useMutation({
    mutationFn: (a: A) => fn(...a),
    onSuccess: (r) => {
      const m = typeof ok === "function" ? ok(r) : ok;
      if (m) say("ok", m);
      void qc.invalidateQueries();
    },
    onError: (e) => {
      say("error", e instanceof ApiError || e instanceof Error ? e.message : String(e));
      void qc.invalidateQueries();
    },
  });
}
