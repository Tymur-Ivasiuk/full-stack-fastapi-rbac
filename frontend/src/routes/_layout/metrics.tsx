import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Suspense } from "react"

import { MetricsService } from "@/client"
import RequirePermission from "@/components/Common/RequirePermission"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

function getMetricsQueryOptions() {
  return {
    queryFn: async () => (await MetricsService.readMetrics()).data,
    queryKey: ["metrics"],
  }
}

export const Route = createFileRoute("/_layout/metrics")({
  component: MetricsPage,
  head: () => ({
    meta: [
      {
        title: "Metrics - FastAPI Template",
      },
    ],
  }),
})

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <span className="text-3xl font-bold">{value}</span>
      </CardContent>
    </Card>
  )
}

function MetricsCards() {
  const { data: metrics } = useSuspenseQuery(getMetricsQueryOptions())

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <StatCard label="Total users" value={metrics.total_users} />
      <StatCard label="Active users" value={metrics.active_users} />
      <StatCard label="Total items" value={metrics.total_items} />
      {Object.entries(metrics.users_by_role).map(([role, count]) => (
        <StatCard key={role} label={`Role: ${role}`} value={count ?? 0} />
      ))}
    </div>
  )
}

function PendingMetrics() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }, (_, index) => (
        <Skeleton key={index} className="h-32" />
      ))}
    </div>
  )
}

function MetricsPage() {
  return (
    <RequirePermission permission="metrics:read">
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Metrics</h1>
          <p className="text-muted-foreground">
            Usage overview across all users
          </p>
        </div>
        <Suspense fallback={<PendingMetrics />}>
          <MetricsCards />
        </Suspense>
      </div>
    </RequirePermission>
  )
}
