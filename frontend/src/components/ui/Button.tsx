import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cx } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  leading?: ReactNode;
  trailing?: ReactNode;
  loading?: boolean;
  full?: boolean;
}

const sizeClass: Record<Size, string> = {
  sm: "px-3 py-2 text-sm rounded-lg",
  md: "px-4 py-2.5 text-[15px] rounded-xl",
  lg: "px-5 py-3.5 text-base rounded-2xl",
};

const variantClass: Record<Variant, string> = {
  primary: "btn-primary",
  secondary: "btn-secondary",
  ghost: "btn-ghost",
  danger: "btn bg-red-500 text-white hover:bg-red-600",
};

export function Button({
  variant = "primary",
  size = "md",
  leading,
  trailing,
  loading,
  full,
  className,
  children,
  disabled,
  ...rest
}: Props) {
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={cx(
        variantClass[variant],
        sizeClass[size],
        full && "w-full",
        loading && "opacity-80",
        className
      )}
    >
      {loading ? (
        <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      ) : (
        leading
      )}
      <span>{children}</span>
      {!loading && trailing}
    </button>
  );
}
