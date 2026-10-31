import { createFileRoute } from "@tanstack/react-router"

import { ROLE_LABELS } from "@/components/Admin/RoleSelect"
import { Badge } from "@/components/ui/badge"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Dashboard - FastAPI Template",
      },
    ],
  }),
})

function Dashboard() {
  const { user: currentUser } = useAuth()

  return (
    <div>
      <div>
        <h1 className="text-2xl truncate max-w-sm">
          Hi, {currentUser?.full_name || currentUser?.email} 👋
        </h1>
        <p className="text-muted-foreground">
          Welcome back, nice to see you again!!!
        </p>
        {currentUser?.role && (
          <p className="mt-4 text-sm text-muted-foreground">
            Signed in as{" "}
            <Badge variant="outline">{ROLE_LABELS[currentUser.role]}</Badge>
          </p>
        )}
      </div>
    </div>
  )
}
