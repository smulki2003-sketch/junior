import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import {
  getRoommateMatches,
  getRoommateQuestionnaire,
  refreshRoommateMatches,
  submitRoommateAnswers,
} from "../api/roommates";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Button } from "../components/ui/Button";
import { ErrorState } from "../components/ui/ErrorState";
import { Skeleton } from "../components/ui/Skeleton";
import { useAuthStore } from "../store/authStore";

export default function RoommatesPage() {
  const user = useAuthStore((state) => state.user);
  const userId = user?.id;
  const [step, setStep] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const [answers, setAnswers] = useState({});

  const questionnaireQuery = useQuery({
    queryKey: ["roommate-questionnaire"],
    queryFn: getRoommateQuestionnaire,
  });

  const questions = Array.isArray(questionnaireQuery.data?.questions) ? questionnaireQuery.data.questions : [];
  const totalSteps = questions.length + 1;
  const currentQuestion = questions[step] || null;

  const submitMutation = useMutation({
    mutationFn: async () => {
      const payload = questions
        .map((question) => ({
          question_id: question.id,
          selected_option_id: answers[question.id],
        }))
        .filter((item) => Number.isFinite(Number(item.selected_option_id)));
      await submitRoommateAnswers(userId, payload);
      await refreshRoommateMatches(userId, { top_n: 10 });
      return getRoommateMatches(userId);
    },
    onSuccess: () => setSubmitted(true),
  });

  const matchesQuery = useQuery({
    queryKey: ["roommates", userId],
    queryFn: () => getRoommateMatches(userId),
    enabled: Boolean(userId) && submitted,
  });

  const missingAnswer = useMemo(
    () => Boolean(currentQuestion && !answers[currentQuestion.id]),
    [currentQuestion, answers]
  );

  if (!submitted) {
    return (
      <PageWrapper>
        {questionnaireQuery.isLoading ? (
          <Skeleton className="mx-auto h-[320px] max-w-2xl" />
        ) : questionnaireQuery.isError ? (
          <ErrorState message="Unable to load roommate questionnaire." onRetry={() => questionnaireQuery.refetch()} />
        ) : (
          <div className="mx-auto max-w-2xl rounded-2xl border border-[var(--border-subtle)] bg-surface p-6">
            <div className="mb-4 h-2 rounded-full bg-elevated">
              <div className="h-full rounded-full bg-primary" style={{ width: `${((step + 1) / totalSteps) * 100}%` }} />
            </div>

            {currentQuestion ? (
              <>
                <h1 className="font-display text-2xl font-bold">{currentQuestion.prompt}</h1>
                <div className="mt-4 grid gap-2">
                  {(currentQuestion.options || []).map((option) => {
                    const active = answers[currentQuestion.id] === option.id;
                    return (
                      <button
                        key={option.id}
                        type="button"
                        onClick={() => setAnswers((prev) => ({ ...prev, [currentQuestion.id]: option.id }))}
                        className={`rounded-xl border p-3 text-left ${active ? "border-primary bg-primary/20" : "border-[var(--border-subtle)]"}`}
                      >
                        {option.label}
                      </button>
                    );
                  })}
                </div>
              </>
            ) : (
              <div className="rounded-xl border border-[var(--border-subtle)] bg-elevated p-4 text-sm">
                <p>Ready to generate roommate matches based on your answers.</p>
              </div>
            )}

            <div className="mt-6 flex justify-between">
              <Button variant="ghost" onClick={() => setStep((s) => Math.max(0, s - 1))}>
                &lt;- Back
              </Button>
              {step < questions.length ? (
                <Button onClick={() => setStep((s) => s + 1)} disabled={missingAnswer}>
                  Next -&gt;
                </Button>
              ) : (
                <Button onClick={() => submitMutation.mutate()} disabled={submitMutation.isPending}>
                  {submitMutation.isPending ? "Submitting..." : "Submit"}
                </Button>
              )}
            </div>
          </div>
        )}
      </PageWrapper>
    );
  }

  const matches = Array.isArray(matchesQuery.data) ? matchesQuery.data : matchesQuery.data?.results || [];

  return (
    <PageWrapper className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-4xl font-bold">Your Roommate Matches</h1>
      </div>

      {matchesQuery.isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      ) : matchesQuery.isError ? (
        <ErrorState message="Unable to load roommate matches." onRetry={() => matchesQuery.refetch()} />
      ) : matches.length === 0 ? (
        <div className="rounded-xl border border-[var(--border-subtle)] bg-surface p-10 text-center">
          <p className="text-[var(--text-secondary)]">No compatible candidates in the same governorate yet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {matches.map((match) => (
            <article key={match.candidate_user_id} className="card rounded-xl border border-[var(--border-subtle)] bg-surface p-4">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-r from-teal to-primary text-sm font-bold">
                  {String(match.candidate_user_id).slice(-2)}
                </div>
                <div className="flex-1">
                  <p className="font-display text-lg">{match.candidate_profile?.full_name || `Student ${match.candidate_user_id}`}</p>
                  <p className="text-xs text-[var(--text-secondary)]">
                    {match.candidate_profile?.phone ? `Phone: ${match.candidate_profile.phone}` : "Phone: N/A"}
                    {" | "}
                    {match.candidate_profile?.governorate ? `Governorate: ${match.candidate_profile.governorate}` : "Governorate: N/A"}
                  </p>
                  <p className="text-xs text-[var(--text-secondary)]">
                    {match.candidate_profile?.university ? `University: ${match.candidate_profile.university}` : "University: N/A"}
                  </p>
                  <div className="mt-2 h-2 rounded-full bg-elevated">
                    <div className="h-full rounded-full bg-gradient-to-r from-teal to-primary" style={{ width: `${Math.round((match.score || 0) * 100)}%` }} />
                  </div>
                </div>
                <p className="font-mono text-sm">{Math.round((match.score || 0) * 100)}%</p>
              </div>
            </article>
          ))}
        </div>
      )}
    </PageWrapper>
  );
}
