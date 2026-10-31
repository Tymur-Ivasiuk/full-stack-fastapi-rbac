import type { Permission } from "@/client"
import useAuth from "./useAuth"

// The backend resolves role -> permissions; the UI only asks "can I?".
const usePermissions = () => {
  const { user } = useAuth()

  const can = (permission: Permission) =>
    user?.permissions.includes(permission) ?? false

  return { can, isLoading: user === undefined }
}

export default usePermissions
