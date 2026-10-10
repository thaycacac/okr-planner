"use client";

import { useTranslations } from "next-intl";
import { useEffect } from "react";
import { toast } from "sonner";

import { CROSS_SITE_EVENT } from "@/lib/api/client";

export function CrossSiteNotice() {
  const t = useTranslations("common");

  useEffect(() => {
    // A fixed id collapses bursts (e.g. autosave retries) into one toast.
    const onCrossSite = () => toast.error(t("crossSiteRequest"), { id: CROSS_SITE_EVENT });
    window.addEventListener(CROSS_SITE_EVENT, onCrossSite);
    return () => window.removeEventListener(CROSS_SITE_EVENT, onCrossSite);
  }, [t]);

  return null;
}
