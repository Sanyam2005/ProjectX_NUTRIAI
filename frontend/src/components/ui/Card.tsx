import type { HTMLAttributes, ReactNode } from "react";
import { cx } from "@/lib/utils";

interface Props extends HTMLAttributes<HTMLDivElement> {
  glow?: boolean;
  glass?: boolean;
  padded?: boolean;
  children?: ReactNode;
}

export function Card({ glow, glass, padded = true, className, children, ...rest }: Props) {
  return (
    <div
      {...rest}
      className={cx(
        glass ? "glass rounded-2xl" : glow ? "card-glow" : "card",
        padded && "p-5",
        className
      )}
    >
      {children}
    </div>
  );
}
