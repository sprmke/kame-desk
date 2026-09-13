import { createFileRoute } from "@tanstack/react-router";
import { PublicBookingPage } from "@/features/booking/pages/PublicBookingPage";

export const Route = createFileRoute("/book/$slug")({
  component: BookRoute,
});

function BookRoute() {
  const { slug } = Route.useParams();
  return <PublicBookingPage slug={slug} />;
}
