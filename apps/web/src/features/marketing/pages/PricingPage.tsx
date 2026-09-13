import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { AuthLayout } from "@/features/auth/components/AuthLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function PricingPage() {
  const { data } = useQuery({
    queryKey: ["public-plans"],
    queryFn: () => api.listPublicPlans(),
  });

  return (
    <AuthLayout title="Plans">
      <div className="grid gap-4">
        {(data ?? []).map((plan) => (
          <Card key={plan.key}>
            <CardContent className="pt-5">
              <p className="font-semibold text-foreground">{plan.name}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                PHP {plan.monthly_php}/month. {plan.trial_days}-day trial.
              </p>
              <p className="mt-2 text-sm text-muted-foreground">
                {plan.included}
              </p>
              <Button asChild className="mt-4">
                <Link to="/register" search={{ plan: plan.key }}>
                  Start trial
                </Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </AuthLayout>
  );
}
