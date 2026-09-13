import { Toaster as Sonner, type ToasterProps } from "sonner";
import { useTheme } from "@/components/theme/ThemeProvider";

function Toaster(props: ToasterProps) {
  const { resolvedTheme } = useTheme();

  return (
    <Sonner
      theme={resolvedTheme}
      position="top-right"
      expand
      closeButton
      duration={5000}
      visibleToasts={5}
      gap={8}
      offset={16}
      className="toaster group"
      icons={{
        success: undefined,
        error: undefined,
        warning: undefined,
        info: undefined,
      }}
      toastOptions={{
        duration: 5000,
        classNames: {
          toast: "dd-toast group",
          title: "dd-toast-title",
          description: "dd-toast-description",
          actionButton: "dd-toast-action",
          cancelButton: "dd-toast-cancel",
          closeButton: "dd-toast-close",
        },
      }}
      {...props}
    />
  );
}

export { Toaster };
