import { AppSidebar, AppTabBar } from "@/components/app-shell/app-nav";
import { AuthGate } from "@/components/app-shell/auth-gate";

export default function ShellLayout({ children }: LayoutProps<"/">) {
  return (
    <>
      <div className="flex flex-1">
        <AppSidebar />
        <main
          id="main"
          tabIndex={-1}
          className="min-w-0 flex-1 px-4 pt-6 pb-24 outline-none md:px-8 md:pb-10"
        >
          <AuthGate>{children}</AuthGate>
        </main>
      </div>
      <AppTabBar />
    </>
  );
}
