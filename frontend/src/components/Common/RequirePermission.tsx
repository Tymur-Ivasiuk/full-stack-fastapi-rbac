import type { ReactNode } from "react"

import type { Permission } from "@/client"
import usePermissions from "@/hooks/usePermissions"
import Forbidden from "./Forbidden"

interface RequirePermissionProps {
  permission: Permission
  children: ReactNode
}

// UX only: the backend enforces the same permission on every endpoint.
const RequirePermission = ({
  permission,
  children,
}: RequirePermissionProps) => {
  const { can, isLoading } = usePermissions()

  if (isLoading) {
    return null
  }
  if (!can(permission)) {
    return <Forbidden />
  }
  return children
}

export default RequirePermission
