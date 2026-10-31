import type { Role } from "@/client"
import { FormControl } from "@/components/ui/form"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

// `satisfies Record<Role, ...>` makes the build fail when the backend adds
// a role (after regenerating the client) until it gets a label here.
export const ROLE_LABELS = {
  admin: "Admin",
  manager: "Manager",
  member: "Member",
} as const satisfies Record<Role, string>

export const ROLES = Object.keys(ROLE_LABELS) as [Role, ...Role[]]

interface RoleSelectProps {
  value?: Role
  onChange: (role: Role) => void
}

export function RoleSelect({ value, onChange }: RoleSelectProps) {
  return (
    <Select value={value} onValueChange={(role) => onChange(role as Role)}>
      <FormControl>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select a role" />
        </SelectTrigger>
      </FormControl>
      <SelectContent>
        {ROLES.map((role) => (
          <SelectItem key={role} value={role}>
            {ROLE_LABELS[role]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
