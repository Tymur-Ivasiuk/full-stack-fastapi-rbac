import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query"
import { createRouter, RouterProvider } from "@tanstack/react-router"
import { AxiosError } from "axios"
import { StrictMode } from "react"
import ReactDOM from "react-dom/client"
import { toast } from "sonner"
import { client } from "./client/client.gen"
import { ThemeProvider } from "./components/theme-provider"
import { Toaster } from "./components/ui/sonner"
import "./index.css"
import { routeTree } from "./routeTree.gen"

client.setConfig({
  baseURL: import.meta.env.VITE_API_URL ?? "",
  auth: () => localStorage.getItem("access_token") || "",
})

const isApiError = (error: Error, status: number) =>
  error instanceof AxiosError && error.response?.status === status

// 401: the session is invalid, so log out. 403: the user is authenticated
// but not allowed, so keep the session and explain instead.
const handleApiError = (error: Error) => {
  if (isApiError(error, 401)) {
    localStorage.removeItem("access_token")
    window.location.href = "/login"
  }
}

const handleQueryError = (error: Error) => {
  handleApiError(error)
  if (isApiError(error, 403)) {
    toast.error("Access denied", {
      description: "You don't have permission to view this data.",
    })
  }
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: handleQueryError,
  }),
  // Mutations already show the backend's error message via handleError.
  mutationCache: new MutationCache({
    onError: handleApiError,
  }),
})

const router = createRouter({ routeTree })
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <Toaster richColors closeButton />
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>,
)
