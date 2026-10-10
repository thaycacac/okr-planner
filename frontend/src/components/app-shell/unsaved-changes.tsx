"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  type ComponentProps,
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

type Guard = {
  setUnsaved: (count: number) => void;
  hasUnsaved: () => boolean;
  /** Runs `leave` right away when nothing is unsaved; otherwise only after the user confirms. */
  confirmLeave: (leave: () => void) => void;
};

const UnsavedChangesContext = createContext<Guard | null>(null);

export function UnsavedChangesProvider({ children }: { children: ReactNode }) {
  const t = useTranslations("unsaved");
  // A ref, not state: forms report on every edit and the shell should not re-render for it.
  const unsaved = useRef(0);
  const [pending, setPending] = useState<{ count: number; leave: () => void } | null>(null);

  useEffect(() => {
    function onBeforeUnload(event: BeforeUnloadEvent) {
      if (unsaved.current > 0) event.preventDefault();
    }
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, []);

  const setUnsaved = useCallback((count: number) => {
    unsaved.current = count;
  }, []);

  const hasUnsaved = useCallback(() => unsaved.current > 0, []);

  const confirmLeave = useCallback((leave: () => void) => {
    if (unsaved.current === 0) leave();
    else setPending({ count: unsaved.current, leave });
  }, []);

  const guard = useMemo(
    () => ({ setUnsaved, hasUnsaved, confirmLeave }),
    [setUnsaved, hasUnsaved, confirmLeave],
  );

  return (
    <UnsavedChangesContext value={guard}>
      {children}
      <AlertDialog open={pending !== null} onOpenChange={(open) => !open && setPending(null)}>
        <AlertDialogContent size="sm">
          <AlertDialogHeader>
            <AlertDialogTitle>{t("title", { count: pending?.count ?? 0 })}</AlertDialogTitle>
            <AlertDialogDescription>{t("body")}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t("stay")}</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={() => {
                const leave = pending?.leave;
                unsaved.current = 0;
                setPending(null);
                leave?.();
              }}
            >
              {t("discard")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </UnsavedChangesContext>
  );
}

const noGuard: Guard = {
  setUnsaved: () => {},
  hasUnsaved: () => false,
  confirmLeave: (leave) => leave(),
};

export function useLeaveGuard(): Guard {
  return useContext(UnsavedChangesContext) ?? noGuard;
}

/** Reports how many unsaved edits the calling form holds; clears on unmount. */
export function useUnsavedChanges(count: number) {
  const { setUnsaved } = useLeaveGuard();
  useEffect(() => {
    setUnsaved(count);
    return () => setUnsaved(0);
  }, [count, setUnsaved]);
}

export function GuardedLink({ href, ...props }: ComponentProps<typeof Link> & { href: string }) {
  const { hasUnsaved, confirmLeave } = useLeaveGuard();
  const router = useRouter();
  return (
    <Link
      href={href}
      onNavigate={(event) => {
        if (!hasUnsaved()) return;
        event.preventDefault();
        confirmLeave(() => router.push(href));
      }}
      {...props}
    />
  );
}
