import { forwardRef } from 'react';
import type { ButtonHTMLAttributes } from 'react';

export type ButtonVariant = 'default' | 'outline' | 'ghost';
export type ButtonSize = 'default' | 'sm';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

/**
 * Local shadcn-style button (ADR 0017): same component contract as shadcn/ui
 * (forwardRef, variant/size props, data-slot) styled with the design tokens.
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'default', size = 'default', type = 'button', className, ...props },
  ref,
) {
  const classes = ['button', `button--${variant}`, `button--${size}`];
  if (className) classes.push(className);
  return (
    <button ref={ref} type={type} data-slot="button" className={classes.join(' ')} {...props} />
  );
});

export default Button;
