import { AuthGate } from "@/components/app-shell/auth-gate";
import { WizardStepper } from "@/components/plan/wizard-stepper";

// The wizard hides the app navigation so the next step is the only way forward (spec S1–S4).
export default function PlanWizardLayout({ children }: LayoutProps<"/plan/new">) {
  return (
    <div className="flex flex-1 flex-col">
      <WizardStepper />
      <main
        id="main"
        tabIndex={-1}
        className="mx-auto w-full max-w-6xl min-w-0 flex-1 px-4 pt-6 pb-32 outline-none md:px-8"
      >
        <AuthGate>{children}</AuthGate>
      </main>
    </div>
  );
}
