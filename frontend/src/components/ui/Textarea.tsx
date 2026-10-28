import { forwardRef } from 'react';
import type { TextareaHTMLAttributes } from 'react';

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>;

/**
 * Local shadcn-style textarea (ADR 0017): same component contract as
 * shadcn/ui (forwardRef, data-slot) styled with the design tokens.
 */
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { className, ...props },
  ref,
) {
  return (
    <textarea
      ref={ref}
      data-slot="textarea"
      className={`textarea${className ? ` ${className}` : ''}`}
      {...props}
    />
  );
});

export default Textarea;
