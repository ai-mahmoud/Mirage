import * as React from "react";
import { motion } from "framer-motion";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input, Label, Select, FieldError } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { createSession } from "@/lib/api-client";

const schema = z.object({
  candidateName: z.string().min(2, "Candidate name is required."),
  interviewType: z.string().min(1, "Interview type is required."),
  position: z.string().optional(),
  department: z.string().optional(),
  observerName: z.string().min(2, "Observer name is required."),
});

export type CreateSessionValues = z.infer<typeof schema>;
export type CreateSessionResult = CreateSessionValues & { sessionId: string };

export function CreateSessionForm({
  onCreate,
  onCancel,
}: {
  onCreate: (result: CreateSessionResult) => void;
  onCancel: () => void;
}) {
  const [submitError, setSubmitError] = React.useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateSessionValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      candidateName: "",
      interviewType: "Technical Interview",
      position: "",
      department: "",
      observerName: "Demo Observer",
    },
  });

  const onSubmit = async (values: CreateSessionValues) => {
    setSubmitError(null);
    try {
      const created = await createSession({
        candidateName: values.candidateName,
        interviewType: values.interviewType,
        position: values.position || undefined,
        department: values.department || undefined,
        observerName: values.observerName,
      });
      onCreate({ ...values, sessionId: created.sessionId });
    } catch {
      setSubmitError(
        "Couldn't reach the behavioral intelligence service. Confirm the backend is running and try again."
      );
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mx-auto max-w-xl">
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Create Session</CardTitle>
            <CardDescription>Initialize a new behavioral observation session.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div>
              <Label htmlFor="candidateName">Candidate Name</Label>
              <Input id="candidateName" placeholder="e.g. Candidate A" {...register("candidateName")} />
              <FieldError>{errors.candidateName?.message}</FieldError>
            </div>

            <div>
              <Label htmlFor="interviewType">Interview Type</Label>
              <Select id="interviewType" {...register("interviewType")}>
                <option>Technical Interview</option>
                <option>Portfolio Review</option>
                <option>Screening Call</option>
                <option>Panel Interview</option>
              </Select>
              <FieldError>{errors.interviewType?.message}</FieldError>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="position">Position (optional)</Label>
                <Input id="position" placeholder="e.g. Backend Engineer" {...register("position")} />
              </div>
              <div>
                <Label htmlFor="department">Department (optional)</Label>
                <Input id="department" placeholder="e.g. Engineering" {...register("department")} />
              </div>
            </div>

            <div>
              <Label htmlFor="observerName">Observer Name</Label>
              <Input id="observerName" {...register("observerName")} />
              <FieldError>{errors.observerName?.message}</FieldError>
            </div>

            {submitError && <p className="text-sm text-crimson-600">{submitError}</p>}

            <div className="flex gap-3 pt-2">
              <Button type="button" variant="secondary" className="flex-1" onClick={onCancel} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button type="submit" className="flex-1" disabled={isSubmitting}>
                {isSubmitting ? "Creating Session…" : "Create Session"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </motion.div>
  );
}
