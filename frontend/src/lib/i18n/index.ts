import { en } from "./en";
import { te } from "./te";
import { useStudioStore } from "../store";

export type Language = "en" | "te";

export const translations = {
  en,
  te,
};

export function useTranslation() {
  const language = useStudioStore((state) => state.language);
  const setLanguage = useStudioStore((state) => state.setLanguage);
  const t = translations[language] || translations.en;

  return { t, language, setLanguage };
}
