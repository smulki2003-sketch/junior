import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { getRoommateQuestionnaire, upsertRoommateQuestionnaire } from "../../api/admin/questionnaires";
import { AdminShell } from "../../components/layout/AdminShell";
import { Button } from "../../components/ui/Button";
import { ErrorState } from "../../components/ui/ErrorState";
import { Skeleton } from "../../components/ui/Skeleton";

function emptyQuestion() {
  return {
    dimension_key: "",
    prompt: "",
    weight: 1,
    options: [
      { label: "Low", numeric_value: 1 },
      { label: "Medium", numeric_value: 3 },
      { label: "High", numeric_value: 5 },
    ],
  };
}

export default function AdminQuestionnairesPage() {
  const query = useQuery({
    queryKey: ["admin-roommate-questionnaire"],
    queryFn: getRoommateQuestionnaire,
  });

  const source = query.data || {};
  const [title, setTitle] = useState("");
  const [questions, setQuestions] = useState([]);
  const [version, setVersion] = useState(1);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (initialized || query.isLoading || query.isError) return;
    setInitialized(true);
    setTitle(source.title || "Roommate Lifestyle Questionnaire");
    setVersion(Number(source.version || 1));
    setQuestions(
      Array.isArray(source.questions) && source.questions.length
        ? source.questions.map((q) => ({
            dimension_key: q.dimension_key || "",
            prompt: q.prompt || "",
            weight: Number(q.weight || 1),
            options: Array.isArray(q.options)
              ? q.options.map((o) => ({ label: o.label || "", numeric_value: Number(o.numeric_value || 0) }))
              : [],
          }))
        : [emptyQuestion()]
    );
  }, [initialized, query.isLoading, query.isError, source.title, source.version, source.questions]);

  const totalQuestions = useMemo(() => questions.length, [questions.length]);

  const saveMutation = useMutation({
    mutationFn: () =>
      upsertRoommateQuestionnaire({
        title: title.trim() || "Roommate Lifestyle Questionnaire",
        version: version < 1 ? 1 : version,
        is_active: true,
        questions: questions.map((question) => ({
          dimension_key: question.dimension_key.trim(),
          prompt: question.prompt.trim(),
          weight: Number(question.weight || 1),
          options: (question.options || [])
            .filter((option) => String(option.label || "").trim())
            .map((option) => ({
              label: String(option.label || "").trim(),
              numeric_value: Number(option.numeric_value || 0),
            })),
        })),
      }),
    onSuccess: () => {
      toast.success("Questionnaire saved");
      setInitialized(false);
      query.refetch();
    },
  });

  return (
    <AdminShell breadcrumb="Moderation / Questionnaires">
      <section className="space-y-4 rounded-[10px] border border-[var(--table-border)] bg-surface p-4">
        <div className="flex items-center justify-between">
          <h1 className="font-display text-xl font-semibold">Roommate Questionnaire</h1>
          <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending || !questions.length}>
            {saveMutation.isPending ? "Saving..." : "Save"}
          </Button>
        </div>

        {query.isLoading ? (
          <Skeleton className="h-[220px]" />
        ) : query.isError ? (
          <ErrorState message="Unable to load questionnaire." onRetry={() => query.refetch()} />
        ) : (
          <>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <label className="text-sm">
                Title
                <input
                  className="mt-1 w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2 text-sm"
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                />
              </label>
              <label className="text-sm">
                Version
                <input
                  type="number"
                  min={1}
                  className="mt-1 w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2 text-sm"
                  value={version}
                  onChange={(event) => setVersion(Number(event.target.value) || 1)}
                />
              </label>
            </div>

            <div className="rounded-md border border-[var(--table-border)] bg-elevated p-3 text-sm text-[var(--text-secondary)]">
              Total questions: {totalQuestions}
            </div>

            <div className="space-y-3">
              {questions.map((question, index) => (
                <div key={index} className="rounded-md border border-[var(--table-border)] bg-elevated p-3">
                  <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                    <input
                      className="rounded-md border border-[var(--border-subtle)] bg-surface px-3 py-2 text-sm"
                      placeholder="dimension_key"
                      value={question.dimension_key}
                      onChange={(event) =>
                        setQuestions((prev) =>
                          prev.map((row, rowIndex) =>
                            rowIndex === index ? { ...row, dimension_key: event.target.value } : row
                          )
                        )
                      }
                    />
                    <input
                      className="rounded-md border border-[var(--border-subtle)] bg-surface px-3 py-2 text-sm md:col-span-2"
                      placeholder="Question prompt"
                      value={question.prompt}
                      onChange={(event) =>
                        setQuestions((prev) =>
                          prev.map((row, rowIndex) =>
                            rowIndex === index ? { ...row, prompt: event.target.value } : row
                          )
                        )
                      }
                    />
                  </div>

                  <div className="mt-2 flex items-center gap-2">
                    <label className="text-xs">
                      Weight
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        className="ml-2 w-24 rounded-md border border-[var(--border-subtle)] bg-surface px-2 py-1 text-sm"
                        value={question.weight}
                        onChange={(event) =>
                          setQuestions((prev) =>
                            prev.map((row, rowIndex) =>
                              rowIndex === index ? { ...row, weight: Number(event.target.value) || 0 } : row
                            )
                          )
                        }
                      />
                    </label>
                    <Button
                      variant="ghost"
                      onClick={() => setQuestions((prev) => prev.filter((_, rowIndex) => rowIndex !== index))}
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              ))}
            </div>

            <Button variant="outline" onClick={() => setQuestions((prev) => [...prev, emptyQuestion()])}>
              Add Question
            </Button>
          </>
        )}
      </section>
    </AdminShell>
  );
}
