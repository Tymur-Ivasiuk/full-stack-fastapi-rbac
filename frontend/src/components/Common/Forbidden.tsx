import { Link } from "@tanstack/react-router"
import { ShieldX } from "lucide-react"

import { Button } from "@/components/ui/button"

const Forbidden = () => {
  return (
    <div
      className="flex flex-col items-center justify-center gap-4 py-24 text-center"
      data-testid="forbidden"
    >
      <ShieldX className="size-12 text-muted-foreground" />
      <h1 className="text-2xl font-bold">Access denied</h1>
      <p className="max-w-md text-muted-foreground">
        Your role doesn't allow you to view this page. If you think you should
        have access, ask an administrator.
      </p>
      <Link to="/">
        <Button>Go to dashboard</Button>
      </Link>
    </div>
  )
}

export default Forbidden
